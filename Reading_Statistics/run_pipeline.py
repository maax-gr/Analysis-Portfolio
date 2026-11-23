"""Rebuild reading statistics from a Goodreads export.

Online genre lookup and refreshing Goodreads dates are explicit opt-in steps.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

from src.cleaning import clean_dataframe, load_raw_csv
from src.enrichment import compute_enrichment, match_scraped_titles_to_raw, merge_read_dates_into_df


def build_enriched(raw: Path, enriched: Path, use_read_dates: bool = False,
                   enrich_genres: bool = False) -> pd.DataFrame:
    """Recalculate read-shelf statistics, preserving existing enrichment by book ID."""
    df_clean, report = clean_dataframe(load_raw_csv(raw))
    if report["invalid_pages_rows"]:
        print("Warning: invalid Number of Pages for rows:")
        for title in report["invalid_pages_rows"]:
            print(" -", title)
    df = df_clean.loc[df_clean["Exclusive Shelf"].eq("read").fillna(False)].copy()

    if enriched.exists():
        previous = pd.read_csv(enriched, dtype=str, keep_default_na=False)
        if "Book Id" not in previous.columns:
            raise ValueError(f"Missing Book Id column in {enriched}")
        previous = previous.loc[previous["Book Id"].ne("")].copy()
        if previous["Book Id"].duplicated().any():
            raise ValueError(f"Duplicate Book Id values in {enriched}")
        previous = previous.set_index("Book Id")
        ids = df["Book Id"].fillna("").astype(str)
        for column, fallback in (("Date Started", "Date Added"), ("Date Finished", "Date Read")):
            if column in previous and fallback in previous:
                values = pd.to_datetime(previous[column], errors="coerce")
                old_fallback = pd.to_datetime(previous[fallback], errors="coerce")
                is_fallback = values.eq(old_fallback)
                if column == "Date Started" and "Date Finished" in previous:
                    old_finished = pd.to_datetime(previous["Date Finished"], errors="coerce")
                    is_fallback |= old_fallback.notna() & old_finished.notna() & (old_fallback > old_finished) & values.eq(old_finished)
                explicit = values.where(values.notna() & ~is_fallback)
                df[column] = pd.to_datetime(ids.map(explicit), errors="coerce")
        for column in ("genre_raw", "genre", "lookup_status", "genre_source"):
            if column in previous:
                df[column] = ids.map(previous[column])

    cache = enriched.parent / "read_dates_cache.csv"
    legacy_cache = enriched.parent / "enriched" / "read_dates_cache.csv"
    legacy_titles = enriched.parent / "enriched" / "read_titles_scrape.csv"
    cache_path = next((path for path in (cache, legacy_cache, legacy_titles) if path.exists()), None)
    if cache_path is not None:
        scraped = pd.read_csv(cache_path, dtype=str, keep_default_na=False)
        cache_map = {
            row.get("key", ""): (row.get("date_started", ""), row.get("date_finished", ""))
            for _, row in scraped.iterrows() if row.get("key", "")
        }
        df = merge_read_dates_into_df(df, cache_map)
        if use_read_dates:
            df = match_scraped_titles_to_raw(df, scraped)
    elif use_read_dates:
        raise FileNotFoundError(f"No read dates cache found in {enriched.parent}")

    df = compute_enrichment(df)
    enriched.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(enriched, index=False)
    if enrich_genres:
        from src.genre_enrichment import enrich_genres_file
        df = enrich_genres_file(enriched)
    return df


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_csv")
    parser.add_argument("enriched_csv")
    parser.add_argument("--use-read-dates", action="store_true", help="Fuzzy-match existing read-date cache")
    parser.add_argument("--refresh-read-dates", action="store_true", help="Scrape new read dates before rebuilding")
    parser.add_argument("--enrich-genres", action="store_true", help="Look up genres online")
    parser.add_argument("--debug-read-dates", action="store_true")
    parser.add_argument("--page-limit", "--max-pages", dest="max_pages", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-read", action="store_true", help="Deprecated: output already contains only read books")
    args = parser.parse_args(argv[1:])

    if args.refresh_read_dates:
        from src.goodreads_title_scraper import scrape_read_titles
        scrape_read_titles(limit=args.limit, headful=True, debug=args.debug_read_dates,
                           delay=args.delay, max_pages=args.max_pages)
    enriched = Path(args.enriched_csv)
    build_enriched(Path(args.raw_csv), enriched,
                   use_read_dates=args.use_read_dates or args.refresh_read_dates,
                   enrich_genres=args.enrich_genres)
    print(f"Wrote enriched CSV to {enriched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
