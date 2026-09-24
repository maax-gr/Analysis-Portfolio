"""Streamlit entry point for Reading Statistics Dashboard.

Implements Milestone M3: fixed "This Year" filter, KPI cards, and two charts
(books per month and pages over time). The app reads from the enriched CSV
produced by the pipeline: `data/enriched_goodreads_library_export.csv`.
"""
from pathlib import Path
import sys
import time
import streamlit as st
import pandas as pd
import plotly.express as px

# Ensure `src/` is importable when running the script directly
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from metrics import books_per_month, pages_over_time
from cleaning import load_raw_csv, clean_dataframe
from enrichment import compute_enrichment


ENRICHED_CSV = ROOT / "data" / "enriched_goodreads_library_export.csv"
RAW_CSV = ROOT / "data" / "raw_goodreads_library_export.csv"


def ensure_enriched(raw: Path, enriched: Path, force: bool = False) -> pd.DataFrame:
    """Ensure an enriched CSV exists by running the pipeline if necessary.

    Behavior:
    - If `force` is True, always re-run the pipeline.
    - If enriched file is missing and raw exists, run the pipeline.
    - If raw exists and is newer than enriched, re-run the pipeline.
    - If raw missing but enriched exists, load enriched.
    - If neither exists, return empty DataFrame.
    """
    # If force-run requested, do it unconditionally (if raw exists)
    if force and raw.exists():
        df_raw = load_raw_csv(raw)
        df_clean, report = clean_dataframe(df_raw)
        df_enriched = compute_enrichment(df_clean)
        enriched.parent.mkdir(parents=True, exist_ok=True)
        df_enriched.to_csv(enriched, index=False)
        return df_enriched

    # If enriched missing but raw exists -> run pipeline
    if (not enriched.exists()) and raw.exists():
        df_raw = load_raw_csv(raw)
        df_clean, report = clean_dataframe(df_raw)
        if report.get("invalid_pages_rows"):
            st.warning("Invalid Number of Pages in these rows:\n" + "\n".join(report["invalid_pages_rows"]))
        df_enriched = compute_enrichment(df_clean)
        enriched.parent.mkdir(parents=True, exist_ok=True)
        df_enriched.to_csv(enriched, index=False)
        return df_enriched

    # If both exist, check timestamps: re-run if raw is newer
    if enriched.exists() and raw.exists():
        enriched_mtime = enriched.stat().st_mtime
        raw_mtime = raw.stat().st_mtime
        if raw_mtime > enriched_mtime:
            # raw changed since enriched was produced
            df_raw = load_raw_csv(raw)
            df_clean, report = clean_dataframe(df_raw)
            if report.get("invalid_pages_rows"):
                st.warning("Invalid Number of Pages in these rows:\n" + "\n".join(report["invalid_pages_rows"]))
            df_enriched = compute_enrichment(df_clean)
            df_enriched.to_csv(enriched, index=False)
            return df_enriched
        # otherwise load existing enriched
        return pd.read_csv(enriched, parse_dates=["Date Added", "Date Read"], keep_default_na=True)

    # If enriched exists but raw missing -> load enriched
    if enriched.exists() and (not raw.exists()):
        return pd.read_csv(enriched, parse_dates=["Date Added", "Date Read"], keep_default_na=True)

    # neither exists
    return pd.DataFrame()


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
    # Slightly smaller title to keep the UI compact
    st.markdown("### Reading Dashboard")

    # Sidebar controls: pipeline and filters
    st.sidebar.header("Data / Pipeline")
    force_run = st.sidebar.button("Re-run cleaning & enrichment")

    # If the user triggered force_run, call ensure_enriched with force=True
    if force_run:
        with st.spinner("Running cleaning & enrichment pipeline..."):
            df = ensure_enriched(RAW_CSV, ENRICHED_CSV, force=True)
            st.success("Pipeline finished.")
    else:
        df = ensure_enriched(RAW_CSV, ENRICHED_CSV, force=False)

    if df.empty:
        st.warning(f"No data available. Place your raw export at {RAW_CSV} and re-run the pipeline.")
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
            pages_start = df_range["Date Added"].min() if "Date Added" in df_range.columns else df_range["Date Read"].min()
            pages_end = df_range["Date Read"].max()

        series_pages = pages_over_time(df_range, start=pages_start, end=pages_end)
        if series_pages.empty:
            st.info("No pages data available for the selected range.")
        else:
            fig2 = px.line(x=series_pages.index, y=series_pages.values, labels={"x": "Date", "y": "Pages read"})
            st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()

