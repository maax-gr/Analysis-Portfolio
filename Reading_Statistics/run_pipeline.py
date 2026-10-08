"""Small runner to execute the cleaning + enrichment pipeline and write enriched CSV.

Features added for M5:
- optional `--use-read-dates` to load or extract `read_dates` and merge into
    the cleaned DataFrame before enrichment
- simple CSV cache support for extracted `read_dates`

Usage:
        python run_pipeline.py [--use-read-dates] [--refresh-read-dates] [--headless] \
                data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv
"""
import sys
from pathlib import Path
import argparse
import pandas as pd

from src.cleaning import load_raw_csv, clean_dataframe
from src.enrichment import compute_enrichment, merge_read_dates_into_df
from src.goodreads_playwright import extract_read_dates


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_csv")
    parser.add_argument("enriched_csv")
    parser.add_argument("--use-read-dates", action="store_true", help="Load or extract read_dates and merge before enrichment")
    parser.add_argument("--refresh-read-dates", action="store_true", help="Ignore cache and re-run extraction for missing items")
    parser.add_argument("--headless", action="store_true", help="Run extractor in headless mode when supported")
    parser.add_argument("--debug-read-dates", action="store_true", help="Enable debug prints in the read_dates extractor")
    parser.add_argument("--max-pages", type=int, default=0, help="Optional page-limit for the extractor (0 = unlimited)")
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

    # Optionally load/extract read_dates and merge into df_clean
    if args.use_read_dates:
        cache_dir = enriched.parent / "enriched"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "read_dates_cache.csv"
        print("Loading read_dates cache (if present):", cache_file)

        def _book_key(row: pd.Series) -> str:
            title = row.get("Title") or ""
            author = row.get("Author") or ""
            # normalize same as extractor
            import re
            s = f"{title} {author}".lower()
            s = re.sub(r"[\"'`\[\]\(\){}:;,\.\?/\\|@#$%^&*_+=<>~<>-]+", "", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        rows = list(df_clean.iterrows())
        if args.only_read:
            rows = [(i, r) for i, r in rows if str(r.get("Exclusive Shelf")).lower() == "read"]
        if args.limit and args.limit > 0:
            rows = rows[: args.limit]
        book_keys = [ _book_key(r) for _, r in rows ]

        cache_map = extract_read_dates(book_keys, cache_path=str(cache_file), headful=not args.headless, debug=args.debug_read_dates, limit=args.limit, refresh=args.refresh_read_dates, page_limit=args.max_pages)
        df_merged = merge_read_dates_into_df(df_clean, cache_map)
    else:
        df_merged = df_clean

    df_enriched = compute_enrichment(df_merged)
    enriched.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.to_csv(enriched, index=False)
    print(f"Wrote enriched CSV to {enriched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
