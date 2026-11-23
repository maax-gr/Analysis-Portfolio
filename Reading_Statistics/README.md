# Reading Statistics Dashboard

The dashboard visualizes a Goodreads CSV export and can optionally merge
reading dates extracted from Goodreads.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run Reading_Dashboard.py
```

Place the Goodreads export at `data/raw_goodreads_library_export.csv`. On
startup, the dashboard creates `data/enriched_goodreads_library_export.csv`
if it is missing. The enriched CSV contains only books on the `read` shelf.

The dashboard compares the read-shelf Book IDs in the raw export with the
enriched file. If they differ, it displays a warning; select **Re-run from raw
data** and confirm to update the enriched file. An existing enriched file is
not automatically overwritten when the raw export changes.

Rebuilding recalculates statistics locally. It does not scrape Goodreads or
look up genres online. Existing genre metadata and reading dates are retained
where possible, and exact matches from `data/read_dates_cache.csv` are reused
when the cache exists. The raw export remains unchanged.

Book counts, ratings and other book-based statistics are filtered by **Date
Read**, not the start date. If Date Read is missing, Date Added is used as a
fallback. Pages over time are allocated to the actual reading interval, so a
book spanning two years can contribute pages to both.

## Optional extraction

Use **Extract reading dates from Goodreads** in the dashboard to launch the
visible browser scraper. When extraction completes, the dashboard matches the
saved cache and recalculates statistics. Install the Playwright browser first
if needed:

```bash
playwright install chromium
```

To run a small extractor smoke test:

```bash
python -m src.goodreads_title_scraper --page-limit 5 --delay 1.0
```

The command-line pipeline also supports explicit online operations:

```bash
python run_pipeline.py data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv
python run_pipeline.py data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv --use-read-dates
python run_pipeline.py data/raw_goodreads_library_export.csv data/enriched_goodreads_library_export.csv --enrich-genres
```

The first command is offline. `--use-read-dates` additionally applies fuzzy
matching to the existing cache; `--enrich-genres` opts into online genre
lookups for all read books. `--refresh-read-dates` explicitly runs the
Goodreads scraper.

## Genre lookup

Select **Look up book genres**, then choose **Look up all books**, **Look up
missing books**, or **Cancel**. Missing means `genre_raw` is empty or an
empty JSON list, regardless of the previous lookup status. The dashboard shows
the current book number and locks while the background lookup runs. The lookup
sends each book's ISBN or title and author to Open Library first and falls back
to Google Books if needed. If Google returns HTTP 429, it is skipped for the
rest of that run. Open Library continues to be tried for remaining books.
Title searches omit subtitles after a colon and trailing parenthesized or
bracketed details; matching also tolerates a leading "The" but still requires
the author to match.

Results are saved in the enriched CSV: `genre_raw` is a JSON list of the
original subject strings, `genre` is the mapped category, and `lookup_status`
is `matched`, `not_found`, or `error`. Matched entries are reused
in missing-book mode when raw subjects are present; empty or failed entries are
retried. Each book is mapped immediately and saved atomically before the next
book is processed. If the run is interrupted, choose missing books to resume.
Refresh failures do not erase previously saved genre data. A normal raw-data rebuild retains
these columns. New results also record their provider in `genre_source`; results
from older runs may have no source recorded. Genre mapping can be recalculated
offline from saved subjects:

```bash
python src/genre_enrichment.py data/enriched_goodreads_library_export.csv --remap-only
```

All requests, including retries, wait at least 1.1 seconds before starting to
stay below Open Library's default rate of one request per second. Transient
network failures are retried once. If Open Library fails for three
consecutive books, the lookup stops after saving progress; retry later. Google
429 errors indicate rate limiting and are not retried during the same run.
If the CSV changes during a lookup, saving stops instead of overwriting the
other changes; already completed checkpoints remain saved.

The current deterministic rules prioritize Historical Fiction and Fantasy
over general thriller or science-fiction terms, and match whole words or
phrases rather than fragments within unrelated words.

## Tests

```bash
python -m unittest discover -s tests -v
```
