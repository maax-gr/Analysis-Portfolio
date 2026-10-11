"""Small runner to execute the cleaning + enrichment pipeline and write enriched CSV.

Features added for M5:
- optional `--use-read-dates` to load or extract `read_dates` and merge into
    the cleaned DataFrame before enrichment
- simple CSV cache support for extracted `read_dates`

Usage:
        python run_pipeline.py [--use-read-dates] [--refresh-read-dates] data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv
"""
import sys
from pathlib import Path
import argparse
import pandas as pd

from src.cleaning import load_raw_csv, clean_dataframe
from src.enrichment import compute_enrichment, match_scraped_titles_to_raw, merge_read_dates_into_df
from src.goodreads_title_scraper import scrape_read_titles


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_csv")
    parser.add_argument("enriched_csv")
    parser.add_argument("--use-read-dates", action="store_true", help="Load or extract read_dates and merge before enrichment")
    parser.add_argument("--refresh-read-dates", action="store_true", help="Ignore cache and re-run extraction for missing items")
    parser.add_argument("--debug-read-dates", action="store_true", help="Enable debug prints in the read_dates extractor")
    parser.add_argument("--page-limit", "--max-pages", dest="max_pages", type=int, default=0, help="Optional page-limit for the extractor (0 = unlimited)")
    parser.add_argument("--delay", type=float, default=1.0, help="Polite delay between page actions (seconds)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of books to scrape (0 = no limit)")
    parser.add_argument("--only-read", action="store_true", help="Only attempt scraping for books with Exclusive Shelf == 'read'")
    args = parser.parse_args(argv[1:])

    raw, enriched = Path(args.raw_csv), Path(args.enriched_csv)
    df_raw = load_raw_csv(raw)
    df_clean, report = clean_dataframe(df_raw)
    if report.get("invalid_pages_rows"):
        print("Warning: invalid Number of Pages for rows:")
        for t in report["invalid_pages_rows"]:
            print(" -", t)

    if args.use_read_dates:
        cache_dir = enriched.parent / "enriched"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "read_dates_cache.csv"
        print("Loading read_dates cache (if present):", cache_file)

        scraped_csv = cache_dir / "read_dates_cache.csv"
        legacy_csv = cache_dir / "read_titles_scrape.csv"

        if args.refresh_read_dates or not (scraped_csv.exists() or legacy_csv.exists()):
            # Live extraction is only used when requested or when no cache exists.
            # The dashboard reads an already-written cache and should not trigger a
            # second browser run while it validates the merge.
            scrape_read_titles(limit=args.limit, headful=True, debug=args.debug_read_dates, delay=args.delay, max_pages=args.max_pages)

        if scraped_csv.exists():
            source_csv = scraped_csv
        elif legacy_csv.exists():
            source_csv = legacy_csv
        else:
            source_csv = None

        if source_csv is not None:
            scraped_df = pd.read_csv(source_csv)
            cache_map = {}
            for _, row in scraped_df.iterrows():
                key = str(row.get("key") or row.get("title") or "")
                if not key:
                    continue
                start = row.get("date_started") or ""
                end = row.get("date_finished") or ""
                cache_map[key] = (start, end)
            df_merged = merge_read_dates_into_df(df_clean, cache_map)
            df_merged = match_scraped_titles_to_raw(df_merged, scraped_df)
        else:
            df_merged = df_clean
    else:
        df_merged = df_clean

    df_merged = df_merged[df_merged["Exclusive Shelf"].fillna("").str.lower() == "read"].copy()
    df_enriched = compute_enrichment(df_merged)
    enriched.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.to_csv(enriched, index=False)
    print(f"Wrote enriched CSV to {enriched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
