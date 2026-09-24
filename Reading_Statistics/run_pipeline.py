"""Small runner to execute the cleaning + enrichment pipeline and write enriched CSV.

Usage:
    python run_pipeline.py data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv
"""
import sys
from pathlib import Path
import pandas as pd

from src.cleaning import load_raw_csv, clean_dataframe
from src.enrichment import compute_enrichment


def main(argv):
    if len(argv) != 3:
        print("Usage: python run_pipeline.py <raw_csv> <enriched_csv>")
        return 1
    raw, enriched = Path(argv[1]), Path(argv[2])
    df_raw = load_raw_csv(raw)
    df_clean, report = clean_dataframe(df_raw)
    if report.get("invalid_pages_rows"):
        print("Warning: invalid Number of Pages for rows:")
        for t in report["invalid_pages_rows"]:
            print(" -", t)
    df_enriched = compute_enrichment(df_clean)
    enriched.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.to_csv(enriched, index=False)
    print(f"Wrote enriched CSV to {enriched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
