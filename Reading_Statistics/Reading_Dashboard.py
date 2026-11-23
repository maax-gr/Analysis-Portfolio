"""Streamlit entry point for Reading Statistics Dashboard.

Implements KPI cards, month-range filtering, Goodreads extraction workflow,
and charts (books per month, pages over time, pages vs rating). The app reads
from the enriched CSV produced by the pipeline:
`data/enriched_goodreads_library_export.csv`.
"""
from pathlib import Path
from collections import Counter
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px

# Ensure `src/` is importable when running the script directly
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from metrics import books_per_month, pages_over_time
from run_pipeline import build_enriched


ENRICHED_CSV = ROOT / "data" / "enriched_goodreads_library_export.csv"
RAW_CSV = ROOT / "data" / "raw_goodreads_library_export.csv"
CACHE_CSV = ROOT / "data" / "read_dates_cache.csv"


def is_process_running(pid: Optional[int]) -> bool:
    if pid is None:
        return False
    # Reap child exits when possible so finished scraper processes don't stay as zombies.
    try:
        finished_pid, _ = os.waitpid(pid, os.WNOHANG)
        if finished_pid == pid:
            return False
    except ChildProcessError:
        # Not a child process in this runtime; fall through to signal probe.
        pass
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def clear_goodreads_extractor_state() -> None:
    """Reset extractor state after scraper completion and merge."""
    st.session_state.pop("goodreads_extractor_pid", None)
    st.session_state.pop("goodreads_extractor_started_at", None)
    st.session_state["goodreads_extractor_status"] = "idle"


def run_pipeline_with_scraped_dates() -> bool:
    """Merge the latest scraper output (read_dates_cache.csv) into the enriched CSV."""
    if not RAW_CSV.exists():
        st.warning(f"Missing raw data at {RAW_CSV}.")
        return False
    if not CACHE_CSV.exists():
        st.warning("Goodreads extraction finished, but no cache file was produced yet.")
        return False

    cmd = [
        sys.executable,
        str(ROOT / "run_pipeline.py"),
        str(RAW_CSV),
        str(ENRICHED_CSV),
        "--use-read-dates",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error("The pipeline refresh failed after the extraction finished.")
        if result.stderr:
            st.code(result.stderr.strip())
        return False

    st.session_state["goodreads_last_run"] = time.time()
    st.success("Goodreads reading dates were merged into the dashboard data.")
    return True


def _show_confirmation_dialog(action: str) -> None:
    """Show a confirmation popup before destructive/long-running actions."""
    message = "Are you sure?"

    def confirm() -> None:
        st.session_state["confirmed_action"] = action
        st.session_state.pop("pending_confirmation", None)

    def cancel() -> None:
        st.session_state.pop("pending_confirmation", None)

    if hasattr(st, "dialog"):
        @st.dialog("Confirm action")
        def _confirm_dialog() -> None:
            st.write(message)
            yes_col, no_col = st.columns(2)
            if yes_col.button("Yes", key=f"{action}_confirm_yes", on_click=confirm):
                st.rerun()
            if no_col.button("No", key=f"{action}_confirm_no", on_click=cancel):
                st.rerun()

        _confirm_dialog()
        return

    st.warning(message)
    yes_col, no_col = st.columns(2)
    if yes_col.button("Yes", key=f"{action}_confirm_yes_fallback", on_click=confirm):
        st.rerun()
    if no_col.button("No", key=f"{action}_confirm_no_fallback", on_click=cancel):
        st.rerun()


def _show_genre_dialog() -> None:
    def choose(action: str) -> None:
        st.session_state["confirmed_action"] = action
        st.session_state.pop("pending_confirmation", None)

    def choices() -> None:
        st.write("Choose which read-shelf books to look up.")
        if st.button("Look up all books", key="genres_all", on_click=choose, args=("genres_all",)):
            st.rerun()
        if st.button("Look up missing books", key="genres_missing", on_click=choose, args=("genres_missing",)):
            st.rerun()
        if st.button("Cancel", key="genres_cancel", on_click=choose, args=("cancel",)):
            st.rerun()

    if hasattr(st, "dialog"):
        st.dialog("Genre lookup")(choices)()
    else:
        choices()


def coerce_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize date-like columns to pandas datetime objects.

    The pipeline writes CSVs with date strings, so when the dashboard reads them
    back it must coerce the relevant columns before performing month filters or
    date arithmetic.
    """
    for col in ["Date Read", "Date Added", "Date Started", "Date Finished"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def launch_goodreads_extractor() -> None:
    """Start the Goodreads scraper in a detached background process.

    The dashboard remains usable while the extraction runs in the background.
    We keep a PID in session state as a failsafe against duplicate clicks.
    """
    running_pid = st.session_state.get("goodreads_extractor_pid")
    if running_pid and is_process_running(running_pid):
        st.info("Goodreads extraction is already running in the background.")
        return

    script = ROOT / "src" / "goodreads_title_scraper.py"
    cmd = [sys.executable, str(script)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    st.session_state["goodreads_extractor_pid"] = proc.pid
    st.session_state["goodreads_extractor_started_at"] = time.time()
    st.session_state["goodreads_extractor_status"] = "running"
    st.toast("Goodreads extraction started in the background.")


def launch_genre_lookup(mode: str) -> None:
    """Run genre lookup in a separate process."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as progress_file:
        progress_path = Path(progress_file.name)
    cmd = [sys.executable, str(ROOT / "src" / "genre_enrichment.py"), str(ENRICHED_CSV),
           "--mode", mode, "--progress-file", str(progress_path)]
    try:
        output = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
    except OSError:
        progress_path.unlink(missing_ok=True)
        raise
    try:
        process = subprocess.Popen(cmd, stdout=output, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
    except OSError:
        output.close()
        progress_path.unlink(missing_ok=True)
        raise
    st.session_state["genre_process"] = process
    st.session_state["genre_output"] = output
    st.session_state["genre_progress_path"] = progress_path


def pages_rating_figure(df: pd.DataFrame, limit_pages: bool):
    """Make the scatter plot match the layout of the other charts."""
    figure = px.scatter(
        df, x="My Rating", y="Number of Pages",
        labels={"My Rating": "Rating", "Number of Pages": "Page count"},
        template="plotly_white",
    )
    figure.update_traces(marker={"size": 20, "opacity": 0.4})
    max_pages = 1000 if limit_pages else max(1, float(df["Number of Pages"].max()) * 1.05)
    figure.update_xaxes(range=[0.5, 5.5])
    figure.update_yaxes(range=[0, max_pages])
    return figure


def ensure_enriched(raw: Path, enriched: Path, force: bool = False) -> pd.DataFrame:
    """Create missing data or explicitly rebuild; never silently overwrite stale data."""
    if force or not enriched.exists():
        if not raw.exists():
            if force:
                raise FileNotFoundError(f"Missing raw data at {raw}")
            return pd.DataFrame()
        return coerce_datetime_columns(build_enriched(raw, enriched))
    if enriched.exists():
        return coerce_datetime_columns(pd.read_csv(enriched, keep_default_na=True))
    return pd.DataFrame()


def data_is_aligned(raw: Path, enriched: Path) -> bool:
    """Compare read-shelf IDs, including duplicate counts, with the enriched file."""
    raw_ids = pd.read_csv(raw, dtype=str, keep_default_na=False, usecols=["Book Id", "Exclusive Shelf"])
    enriched_ids = pd.read_csv(enriched, dtype=str, keep_default_na=False, usecols=["Book Id"])
    read_ids = raw_ids.loc[raw_ids["Exclusive Shelf"].str.strip().str.lower().eq("read"), "Book Id"].str.strip()
    output_ids = enriched_ids["Book Id"].str.strip()
    return not read_ids.eq("").any() and not output_ids.eq("").any() and Counter(read_ids) == Counter(output_ids)


def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute KPI values from a DataFrame filtered to the desired range.

    Returns a dict with: books_read, total_pages, avg_rating, avg_pages_per_book.
    """
    k = {}
    # Count books explicitly on the 'read' shelf
    mask = df["Exclusive Shelf"].notna() & (df["Exclusive Shelf"] == "read")
    df_read = df.loc[mask]
    k["books_read"] = int(df_read.shape[0])

    # Total pages (skip missing values)
    if "Number of Pages" in df_read.columns:
        total_pages = pd.to_numeric(df_read["Number of Pages"], errors="coerce").sum(min_count=1)
        k["total_pages"] = int(total_pages) if not pd.isna(total_pages) else 0
    else:
        k["total_pages"] = 0

    # Average rating (rounded to 1 decimal). Ratings stored as integers 1-5 per spec.
    if "My Rating" in df_read.columns:
        avg_rating = pd.to_numeric(df_read["My Rating"], errors="coerce").mean()
        k["avg_rating"] = round(float(avg_rating), 1) if not pd.isna(avg_rating) else None
    else:
        k["avg_rating"] = None

    # Average pages per book (rounded to int)
    if "Number of Pages" in df_read.columns:
        avg_pages = pd.to_numeric(df_read["Number of Pages"], errors="coerce").mean()
        k["avg_pages_per_book"] = int(round(avg_pages)) if not pd.isna(avg_pages) else None
    else:
        k["avg_pages_per_book"] = None

    return k


def main() -> None:
    st.set_page_config(page_title="Reading Dashboard", layout="wide")
    st.markdown("### Reading Dashboard")
    st.session_state.setdefault("pending_confirmation", None)
    st.session_state.setdefault("confirmed_action", None)

    genre_process = st.session_state.get("genre_process")
    if genre_process is not None:
        if genre_process.poll() is None:
            path = st.session_state.get("genre_progress_path")
            if path:
                try:
                    if not path.stat().st_size:
                        st.info("Preparing genre lookup...")
                    else:
                        progress = json.loads(path.read_text(encoding="utf-8"))
                        completed, total, current = progress["completed"], progress["total"], progress["current"]
                        label = f"Looking up book {current} of {total}" if current else f"Completed {completed} of {total} books"
                        st.progress(completed / total if total else 0.0, text=label)
                except (OSError, ValueError, KeyError) as exc:
                    st.warning(f"Could not read lookup progress: {exc}")
            else:
                st.info("Preparing genre lookup...")
            with st.sidebar:
                st.status("Genre lookup running", state="running")
                st.write("Looking up genres for all read books.")
            st.info("Dashboard is temporarily locked while genre lookup is running.")
            with st.spinner("Looking up book genres..."):
                time.sleep(2)
            st.rerun()
            return
        genre_process.wait()
        output = st.session_state.pop("genre_output")
        output.seek(0)
        messages = output.read().strip()
        output.close()
        st.session_state.pop("genre_process", None)
        path = st.session_state.pop("genre_progress_path", None)
        if path:
            path.unlink(missing_ok=True)
        if genre_process.returncode != 0:
            st.error("Genre lookup failed. Check the enriched file and error details below.")
            if messages:
                st.code(messages)
            return
        lines = messages.splitlines()
        if lines:
            st.success(lines[-1])
        if len(lines) > 1:
            st.warning("Some genre lookups reported problems or returned no new subjects.")
            st.code("\n".join(lines[:-1]))

    running_pid = st.session_state.get("goodreads_extractor_pid")
    extractor_status = st.session_state.get("goodreads_extractor_status", "idle")

    if extractor_status == "running" and running_pid:
        if is_process_running(running_pid):
            with st.sidebar:
                st.status("🔄 Goodreads extraction running", state="running")
                st.write("Scraping titles and dates from Goodreads.")
            st.info("Dashboard is temporarily locked while Goodreads extraction is running.")
            with st.spinner("Extracting Goodreads read dates..."):
                time.sleep(2)
            st.rerun()
            return
        st.session_state["goodreads_extractor_status"] = "matching"
        extractor_status = "matching"

    if extractor_status == "matching":
        with st.sidebar:
            st.status("🔄 Matching scraped dates and recalculating dashboard data", state="running")
            st.write("Extraction finished; now updating dates and metrics.")
        st.info("Dashboard is temporarily locked while scraped data is merged.")
        with st.spinner("Matching Goodreads dates to the export and recalculating metrics..."):
            merged = run_pipeline_with_scraped_dates()
        clear_goodreads_extractor_state()
        if merged:
            st.rerun()
        return

    # Sidebar controls: pipeline and filters
    st.sidebar.header("Data / Pipeline")
    request_rebuild = st.sidebar.button("Re-run from raw data")

    extractor_is_running = bool(running_pid and is_process_running(running_pid))

    request_extract = st.sidebar.button(
        "Extract reading dates from Goodreads",
        key="goodreads_scraper_button",
        disabled=extractor_is_running or extractor_status in {"running", "matching"},
    )
    request_genres = st.sidebar.button("Look up book genres")
    if request_rebuild:
        st.session_state["pending_confirmation"] = "rebuild"
        st.rerun()
        return
    if request_extract:
        st.session_state["pending_confirmation"] = "extract"
        st.rerun()
        return
    if request_genres:
        st.session_state["pending_confirmation"] = "genres"
        st.rerun()
        return

    pending_confirmation = st.session_state.get("pending_confirmation")
    if pending_confirmation in {"extract", "rebuild", "genres"}:
        # Treat dialog dismissal via the "X" as "No" by clearing pending state
        # before opening the dialog; only an explicit "Yes" sets confirmed_action.
        st.session_state.pop("pending_confirmation", None)
        if pending_confirmation == "genres":
            _show_genre_dialog()
        else:
            _show_confirmation_dialog(pending_confirmation)
        return

    confirmed_action = st.session_state.pop("confirmed_action", None)
    force_run = confirmed_action == "rebuild"
    run_extract = confirmed_action == "extract"

    if run_extract:
        launch_goodreads_extractor()
        st.rerun()
        return
    if confirmed_action in {"genres_all", "genres_missing"}:
        try:
            ensure_enriched(RAW_CSV, ENRICHED_CSV)
            if not ENRICHED_CSV.exists():
                raise FileNotFoundError(f"Missing enriched data at {ENRICHED_CSV}.")
            launch_genre_lookup("all" if confirmed_action == "genres_all" else "missing")
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            st.error(f"Could not start genre lookup: {exc}")
            return
        st.rerun()
        return

    # If the user triggered force_run, rebuild the enriched dataset from the raw CSV.
    try:
        if force_run:
            with st.spinner("Rebuilding enriched data from raw Goodreads export..."):
                df = ensure_enriched(RAW_CSV, ENRICHED_CSV, force=True)
                st.success("Raw-data rebuild finished.")
        else:
            df = ensure_enriched(RAW_CSV, ENRICHED_CSV)
        if RAW_CSV.exists() and ENRICHED_CSV.exists():
            if not data_is_aligned(RAW_CSV, ENRICHED_CSV):
                st.warning("Raw and enriched data are not aligned. Consider re-running from raw data.")
        elif not RAW_CSV.exists():
            st.warning(f"Cannot check data alignment: missing raw data at {RAW_CSV}.")
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"Could not load or rebuild reading data: {exc}")
        return

    if df.empty:
        if ENRICHED_CSV.exists():
            st.info("No books on the read shelf are available.")
        else:
            st.warning(f"No data available. Place your raw export at {RAW_CSV} and re-run the pipeline.")
        return

    df = df.loc[df["Exclusive Shelf"].fillna("").str.strip().str.lower().eq("read")].copy()
    if df.empty:
        st.info("No books on the read shelf are available.")
        return

    # --- M4: Interactive Month-Range Filters ---
    st.sidebar.header("Filters")
    # Determine global min/max months from data (based on Date Read)
    min_date = df["Date Read"].min()
    max_date = df["Date Read"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        st.sidebar.info("No Date Read values found in data; filters disabled.")
        start_month = None
        end_month = None
    else:
        # Convert to first-of-month for consistent month-range selection
        min_month = pd.Timestamp(year=min_date.year, month=min_date.month, day=1)
        max_month = pd.Timestamp(year=max_date.year, month=max_date.month, day=1)

        # Presets
        preset = st.sidebar.selectbox("Preset range", ["This Year", "Last Year", "Last 3 Months", "Custom"], index=0)
        today = pd.Timestamp.now().normalize()
        if preset == "This Year":
            start_month = pd.Timestamp(year=today.year, month=1, day=1)
            end_month = today
        elif preset == "Last Year":
            start_month = pd.Timestamp(year=today.year - 1, month=1, day=1)
            end_month = pd.Timestamp(year=today.year - 1, month=12, day=31)
        elif preset == "Last 3 Months":
            end_month = today
            start_month = (today - pd.Timedelta(days=90)).normalize()
        else:
            # Custom: allow month selection using date_input but only show month granularity
            start_month = st.sidebar.date_input("Start month", value=min_month, min_value=min_month, max_value=max_month)
            end_month = st.sidebar.date_input("End month", value=max_month, min_value=min_month, max_value=max_month)

        # Validation: ensure start <= end
        if pd.to_datetime(start_month) > pd.to_datetime(end_month):
            st.sidebar.error("Filter range is incompatible: start is after end.")
            return

    # Convert start_month/end_month to timestamps for filtering: use start of month and end of month
    if min_date is not None and not pd.isna(min_date):
        if isinstance(start_month, pd.Timestamp):
            start_ts = pd.Timestamp(start_month.year, start_month.month, 1)
        else:
            start_ts = pd.to_datetime(start_month).normalize()
        if isinstance(end_month, pd.Timestamp):
            # use end of day for end month
            end_ts = pd.to_datetime(end_month).normalize() + pd.offsets.MonthEnd(0)
        else:
            end_ts = pd.to_datetime(end_month).normalize() + pd.offsets.MonthEnd(0)

    # Apply filter to data based on the selected start_ts/end_ts
    if min_date is not None and not pd.isna(min_date):
        mask_range = df["Date Read"].notna() & (df["Date Read"] >= start_ts) & (df["Date Read"] <= end_ts)
        df_range = df.loc[mask_range].copy()
    else:
        df_range = df.copy()

    # KPI cards
    kpis = compute_kpis(df_range)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Books read", kpis.get("books_read", 0))
    col2.metric("Total pages read", kpis.get("total_pages", 0))
    avg_rating = kpis.get("avg_rating")
    col3.metric("Average rating", f"{avg_rating:.1f}" if avg_rating is not None else "—")
    avg_pages = kpis.get("avg_pages_per_book")
    col4.metric("Avg pages/book", f"{avg_pages}" if avg_pages is not None else "—")

    st.markdown("---")

    # Charts area
    # Place the two charts side-by-side to make the UI more compact
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Books read per month")
        series_books = books_per_month(df_range)
        if series_books.empty:
            st.info("No books in range to display the chart.")
        else:
            fig1 = px.bar(x=series_books.index, y=series_books.values, labels={"x": "Month", "y": "Books read"})
            # Format x-axis ticks as MM/YY
            fig1.update_xaxes(tickformat="%m/%y")
            st.plotly_chart(fig1, use_container_width=True)

    with right_col:
        st.subheader("Pages read over time")
        # Use the filtered range for the pages-over-time calculation so the
        # timeseries reflects the user's selected months.
        # If start_ts/end_ts are not defined for any reason, fall back to the
        # full-data min/max.
        try:
            pages_start = start_ts
            pages_end = end_ts
        except NameError:
            pages_start = df_range["Date Started"].min() if "Date Started" in df_range.columns else df_range["Date Read"].min()
            pages_end = df_range["Date Finished"].max() if "Date Finished" in df_range.columns else df_range["Date Read"].max()

        series_pages = pages_over_time(df, start=pages_start, end=pages_end)
        if series_pages.empty:
            st.info("No pages data available for the selected range.")
        else:
            fig2 = px.line(x=series_pages.index, y=series_pages.values, labels={"x": "Date", "y": "Pages read"})
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    scatter_col, _ = st.columns([1, 1])
    with scatter_col:
        st.subheader("Pages vs Rating")
        limit_pages_1000 = st.checkbox("Limit pages axis to 1000", value=False, key="limit_pages_1000")
        scatter_df = df_range.copy()
        scatter_df["Number of Pages"] = pd.to_numeric(scatter_df["Number of Pages"], errors="coerce")
        scatter_df["My Rating"] = pd.to_numeric(scatter_df["My Rating"], errors="coerce")
        scatter_df = scatter_df.dropna(subset=["Number of Pages", "My Rating"])
        if scatter_df.empty:
            st.info("No page/rating pairs available for the selected range.")
        else:
            fig3 = pages_rating_figure(scatter_df, limit_pages_1000)
            st.plotly_chart(fig3, use_container_width=True)


if __name__ == "__main__":
    main()
