# Reading Statistics Dashboard: Project Spec

Comments are indicated as `{{ comment }}` and are not subject of the current implementation. Ignore while working on the code. Comments can also span multiple lines.

## 1. Overview

**Purpose:** 
- Build a Dashboard that shows my reading statistics
- I want to see how many books and pages I have read recently
- I want to see some statistics about which types of books I enjoy most (authors, genres, etc.)

**Primary user(s):** 
- me
- would be nice to have the dashboard accessible through github, so I can show it to friends

**Out of scope:** 
- Lookup of missing or additional data (will be added in a later iteration)
- stripping data from different or mulitple account (only work with the provided csv file)
- live sync
- mobile compatability
- personalized recommendations (only show statistics)


## 2. Tech Stack & Constraints
- Coding language: Python
- Typical Python packages/libraries
    * data handling: Pandas
    * Dashboard framework: use Streamlit; must refresh automatically, when e.g. changing filters; must be possible to open in GitHub online
    * charts: define together (matplotlib, plotly, altair)
  * scraping: Playwright (optional, offline extraction only)
- Compatability with GitHub

- Use `playwright` Python package and `python -m playwright install` to install browsers.
- Extraction must be an offline pipeline step (never run from the Streamlit dashboard at runtime). The extractor may run headful for interactive login or headless with stored cookies/session for automated runs.
- Extractor responsibilities:
  - Navigate to `https://www.goodreads.com/review/list` (user's My Books list), paginate through pages, and visit per-row `review/show/...` view pages to read the "Reading process" block.
  - Parse lines with date + action (examples: "September 23, 2026 – Started Reading", "January 9, 2023 – Shelved", "February 11, 2026 – Finished Reading").
  - Normalize dates to `YYYY/MM/DD`, record sessions as `START,END` and store multiple sessions separated by `;` in a cache CSV (`data/enriched/read_dates_cache.csv`).
  - Provide a `--headless` toggle, `--limit` to limit number of books to scan, and a `--debug`/`--verbose` mode that prints visited URLs and matched lines for troubleshooting.

Security & etiquette notes:
- Treat the extractor as a personal automation tool; respect Goodreads' terms of service and use conservative delays (`0.5–1s`) between page navigations.
- Do not embed credentials in code; use interactive login (headful) or a local cookie/session export that is not committed.
 
Playwright details (offline extractor only):
- Use `playwright` Python package and `python -m playwright install` to install browsers.
- Extraction must be an offline pipeline step (never run from the Streamlit dashboard at runtime). The extractor should prefer interactive headful login only and must not persist or commit any login/session cookies.
- Extractor responsibilities:
  - Navigate to `https://www.goodreads.com/review/list` (user's My Books list), paginate through pages, and visit per-row `review/show/...` view pages to read the "Reading process" block.
  - Parse lines with date + action (examples: "September 23, 2026 – Started Reading", "February 11, 2026 – Finished Reading"). Do not treat `Shelved` as a session end marker.
  - Normalize dates to `YYYY/MM/DD` and record only the most recent reading session (one `START,END` pair) per book in the cache.
  - Provide CLI options: `--headless`, `--limit N`, `--debug`/`--verbose`, and `--delay SECONDS` (default `0.6`).
  - Output cache CSV: `data/enriched/read_dates_cache.csv` with columns `book_key,date_started,date_finished` (single most-recent session only).
  - Default polite delay between page navigations: `0.6s` (configurable via `--delay`).
  - Debug outputs: `data/enriched/read_dates_debug.log` and per-book snippets in `data/enriched/read_dates_snippets/` when `--debug` is enabled.

Security & etiquette notes:
- Treat the extractor as a personal automation tool; respect Goodreads' terms of service and use conservative delays between page navigations.
- Do not persist or commit login/session cookies. The extractor may prompt for interactive login (headful) but must not write session cookies to disk.
- Use `playwright` Python package and `python -m playwright install` to install browsers.
- Extraction must be an offline pipeline step (never run from the Streamlit dashboard at runtime). The extractor may run headful for interactive login or headless with stored cookies/session for automated runs.
- Extractor responsibilities:
  - Navigate to `https://www.goodreads.com/review/list` (user's My Books list), paginate through pages, and visit per-row `review/show/...` view pages to read the "Reading process" block.
  - Parse lines with date + action (examples: "September 23, 2026 – Started Reading", "January 9, 2023 – Shelved", "February 11, 2026 – Finished Reading").
  - Normalize dates to `YYYY/MM/DD`, record sessions as `START,END` and store multiple sessions separated by `;` in a cache CSV (`data/enriched/read_dates_cache.csv`).
  - Provide a `--headless` toggle, `--limit` to limit number of books to scan, and a `--debug`/`--verbose` mode that prints visited URLs and matched lines for troubleshooting.

Security & etiquette notes:
- Treat the extractor as a personal automation tool; respect Goodreads' terms of service and use conservative delays (`0.5–1s`) between page navigations.
- Do not embed credentials in code; use interactive login (headful) or a local cookie/session export that is not committed.

**Constraints:**
- The dashboard reads only from `data/enriched_goodreads_library_export.csv` and makes **no API calls at runtime**.
- enrichment reads from `data/raw_goodreads_library_export.csv`
- Must run when executing the .py file
- charts must update while running .py file

## 3. Repository Structure

data/
  raw_goodreads_library_export.csv            # Goodreads export (gitignored)
  enriched_goodreads_library_export.csv       # output of enrichment
notebooks/        # exploration only
src/
  cleaning.py     # load + clean Goodreads CSV
  enrichment.py   # genre lookup + caching
  genres.py       # genre mapping rules
  metrics.py      # aggregation function used in charts
Reading_Dashboard.py      # dashboard entry point
SPEC_Reading_Dashboard.md
README.md

## 4. Data

### 4.1 Input: Goodreads export
For every row on the review list page:
- Check that the row's `shelves` contains `read` (or the row's `Exclusive Shelf` equals `read`). Only rows on the `read` shelf count for scraping.
- Determine the `book_key` for matching as the normalized `Title + Author` for the row. Normalization rules: lowercase, strip punctuation, collapse whitespace, and trim surrounding quotes.

- Match strategy:
  - Always use normalized `Title + Author` as the canonical `book_key` for cache and for matching the raw CSV.
  - Matching order: exact normalized `Title + Author` → exact normalized Title-only → normalized Title-only contains match.
  - Do not use fuzzy string-distance matching to avoid false positives.
- Open the per-row "View" link (`/review/show/<id>`) when present to read the "Reading process" block, but do not use the review id as the cache key.

  - Output cache CSV: `data/enriched/read_dates_cache.csv` with columns `book_key,date_started,date_finished` (single most-recent session only). `book_key` MUST be the normalized `Title + Author` string used to match the raw CSV.
**File:** `data/raw_goodreads_library_export.csv`
- includes many columumns which can be ommited in the python variable (do not delete in raw file)
- keep only the following (column | type | cleaning rule):
  * Title | str | strip `"`; not all titles have these signs
  * Author | str | nothing
  * Author l-f | str | strip `"`
  * ISBN | str | Strip `=""` and `"""` wrappers 
  * ISBN13 | str | Strip `=""` and `"""` wrappers
  * My Rating | int | 0 means unrated → treat as null |
  * Publisher | str | nothing
  * Number of Pages | int | nothing
  * Year Published | int | nothing
  * Original Publication Year | int | nothing
  * Date Read | date yyyy/mm/dd | nothing 
  * Date Added | date yyyy/mm/dd | nothing
  * Exclusive Shelf | str | nothing
  * My Review | str | strip `"` if present 

All other fields:
- if empty: set to null

Which books count in the stats?
- books with 'Exclusive Shelf == "read"'


### 4.2 Goodreads Scraper

starting point:
https://www.goodreads.com/review/list?shelf=read
The site shows ~20 books (rows) and the following columns:
cover, title, author, avg rating, rating, shelves, review, date read, date added

For every row on the review list page:
- Open the read shelf explicitly (`?shelf=read`) before scraping.
- Save the visible `Title` and `Author` for every row encountered on the read shelf, even if the row is not yet matched to the raw CSV.
- Open the per-row "View" link (`/review/show/<id>`) and parse the "Reading process" block for `Started Reading` / `Finished Reading` dates.
- Store the result as a pair of dates for that book and keep the raw title/author record in a scraped CSV for later matching.

Scraper output:
- The extractor writes `data/enriched/read_titles_scrape.csv` with columns:
  `title,author,date_started,date_finished`
- It also writes a cache CSV at `data/enriched/read_dates_cache.csv` keyed by normalized `Title + Author`.

Matching algorithm (runs after extraction finishes):
- Build the canonical matching key for each row as normalized `Title + Author` using the same logic as the extractor: lowercase, strip punctuation, collapse whitespace, trim surrounding quotes.
- For each scraped book, look up the matching raw CSV row by exact normalized `Title + Author`.
- If the exact match is missing, fall back to the title-only normalized string only when needed; avoid fuzzy matching.
- When a match is found, copy the extracted `Date Started` and `Date Finished` to the corresponding raw row and keep the original `Date Added` / `Date Read` values as the fallback when the scraper data is empty.
- This match happens in the pipeline after the scraper completes; it is not performed inside the browser loop itself.

**Example 1:**
September 23, 2026 – Started Reading
September 23, 2026 – Shelved
September 28, 2026 – Finished Reading

**Example 2:**
January 9, 2023 – Shelved
January 9, 2023 – Shelved as: to-read
February 1, 2026 – Started Reading
February 1, 2026 – Shelved as: weddingbookshelf
February 1, 2026 – Shelved as: non-fiction
February 1, 2026 – page 60  21.9%
February 11, 2026 – Finished Reading

From the "Reading process" block extract:
- `Started Reading` → `Date Started`
- `Finished Reading` → `Date Finished`

Parsing rules and fallbacks:
- Accept the date formats like `MonthName DD, YYYY` or `MonthName D, YYYY` with full month names (e.g. "September 23, 2026" or "Sep 6, 2026").
- Accept different dash characters (`-`, `–`, `—`) and minor variations in action text (e.g. `Started`, `Started Reading`, `Finished`, `Finished Reading`). Do not treat `Shelved` as a session end marker.
- If multiple sessions are present, select only the most recent finished session (the session with the latest `Finished` date) and record that single `START,END` pair in the cache and enrichment output.
- If `Started Reading` or `Finished Reading` cannot be found for a book, the enrichment step must fall back to SPEC rules in 4.3 (Date Added / Date Read fallback).

Page navigation:
- Each review list page shows ~20 rows. After visiting every row's view page on the current page, click the `next` link and repeat until there is no `next` link.
- The extractor must visit each row's view page before paginating away to avoid missing per-row `Reading process` content. Honor the polite delay (default `1.0s`) between navigations.



### 4.3 Enriched output
**File:** `data/enriched_goodreads_library_export.csv`
Keep only books with 'Exclusive Shelf == "read"'
Remove all other books with 'Exclusive Shelf == "to-read"' or 'Exclusive Shelf == "currently-reading"'

Additional columns (Column | Type | Description ):
* Date Started | date yyyy/mm/dd | 
  - Primarily derived from Goodreads 'Started Reading'. See 4.2 Goodreads Scraper for explanation on how to acquire.
  - if it cannot be found by Scraper, set to same date as "Date Added"

* Date Finished | date yyyy/mm/dd |
  - Primarily derived from Goodreads 'Finished Reading'. See 4.2 Goodreads Scraper for explanation on how to acquire.
  - if it cannot be found by Scraper, set to same date as "Date Read"



### 4.4 Additional stats to calculate
Days until finished | int | counting the days between `Date Started` and `Date Finished` (derived columns)
Average pages read per day | float | `Number of Pages` / `Days until finished`
  - if Number of pages is missing -> set to Null
  - if `Days until finished` = 0 -> set to Null
"pages read on day":
  * Calculate for every day between min `Date Started` (from entire book list) and current date, how many pages were read
    - algorithm example: iterate through each day, check if there are any books with `Date Started` <= iteration_day AND `Date Finished` >= iteration_day, add "average pages read per day" to "pages read on day"
  * only use books where "average pages read per day" is not Null

Multiple readings handling:
  * The enriched CSV stores all detected reading sessions in `read_dates` as described above.
  * For per-book KPIs and the pages/time allocation algorithm we use the most recent reading session (i.e. the session with the latest END_DATE). This keeps calculations intuitive for re-reads while preserving full history for later analysis. If you prefer another policy (earliest reading, count all readings separately, or split into multiple rows) we can change this later.
  

{{ 
Additional columns (Column | Type | Description ):
* genre_raw | list[str] | Raw categories/subjects from the API 
* genre | str | Mapped to one of my broad genres (see 5.3)
* lookup_status | str | matched / not_found }}


{{ ## 5. Genre Enrichment

### 5.1 Sources & order of attempts
1. TODO (e.g. Google Books by ISBN13)
2. TODO (e.g. Open Library by ISBN)
3. TODO (fallback: title + author search)
4. Manual overrides file: `data/manual_genres.csv` (title/ISBN → genre)

### 5.2 Behaviour
- Cache every response (TODO: SQLite / CSV / JSON) so each book is looked up once.
- Rate limiting: TODO (e.g. 1 request/sec, set a User-Agent)
- Failures: log unmatched books to `data/enriched/unmatched.csv`; do not crash.
- Re-running should skip already-cached books unless `--refresh` is passed.
- API keys: read from environment variables / `.env` (never committed). TODO: list variable names.

### 5.3 Genre mapping
> Map messy raw categories to a small, fixed set. One primary genre per book.

| My genre | Raw terms that map to it (case-insensitive contains) |
|---|---|
| Crime / Mystery | detective, mystery, thriller, TODO |
| Science Fiction | TODO |
| Fantasy | TODO |
| Literary Fiction | TODO |
| Non-fiction: History | TODO |
| Non-fiction: Science | TODO |
| Biography / Memoir | TODO |
| TODO | TODO |
| Other | fallback when nothing matches |

**Conflict rule when several match:** TODO (e.g. first match in the table order wins) }}


## 6. Dashboard Requirements

### 6.1 Global filters (sidebar)
- Read in Month-Range
  * choose start and end month of range
  * possible to choose any month from min(date read) to max(date read)
  Presets:
    * Option "This Year" (shows all data from current calender year; derive from current date; e.g. 1st Jan 2026 to today)
    * Option "Last Year" (shows all data from Previous year; derive from current year - 1)
    * Option "Last 3 Months" (shows all data from last 90 days; derive from current date)
  * default: "This Year"
  * if Filter is not filled out correctly (e.g. earlier date in "from" and later date in "to") -> popup message: "Filter range is incompatible". Once message is clicked away by the user, the user can enter a new filter range.

{{ - [ ] Genre (multi-select)
- [ ] Rating (range)
- [ ] TODO }}

### 6.2 KPI cards (top row)
- Books read (int)
- Total pages read (int)
- Average rating (float, round to 1 decimal)
- Average pages per book (int, round to int)
Show all stats for filtered range

### 6.3 Charts
1. Books read per month
  * aggregate on "date read"
  -> it does not matter if "date added" is in a previous month. Only count "date read"
  * Bar chart. time on x-axis, number of books on y-axis. One bar per month.
  * takes global filter into account
2. Pages read over time
  * Line Chart. Time Series on x-axis, "pages read on day" on y-axis

### 6.5 Layout & style
- single page to begin with (might be modified when further charts are added)
- KPI section should occupy no more than 25% of available space at the top
- Theme & colors: tbd. Start with grayscale
- Chart titles on top of chart. Centered around the middle of each graph. Axis titles centered around middle of axis. 
 - Chart layout: two main charts should be presented side-by-side in the same row
   - Left: `Books read per month` (bar chart)
   - Right: `Pages read over time` (line chart)
 - KPI section should occupy no more than 25% of available space at the top
 - Theme & colors: tbd. Start with grayscale
 - Chart titles on top of chart. Centered around the middle of each graph. Axis titles centered around middle of axis.
   - x-axis label for "Pages read over time": when range is more than 3 Months: Display only the first day of each month.
   - x-axis label for "Books read per month": Use format MM/YY. For example 09/26 for september 2026


## 7. Code Standards (for Copilot)
- Type hints on all functions; short docstrings.
- Pure functions in `src/` (no Streamlit/UI imports); `app.py` only handles layout and calls `src/`.
- Aggregation logic lives in `src/metrics.py` -> Question: Is that necessary? Can it not b determined on the fly?
- No hard-coded file paths in functions; use a config constant or argument.
- Prefer small functions 


## 8. Milestones
M1 | Repo setup, create and write README
M2 | Build data cleaning pipeline & enrichment & metrics calculation
M3 | Dashboard v1: KPIs, Charts 1 & 2; fixed filter to "This Year"; no possibility to change filter at this stage
M4 | Dashboard v2: add functional filter as described

M5 | Implement `read_dates` extraction (Playwright)
  - Create a Playwright-based extractor that opens Goodreads edit/review pages, supports interactive login (headful), parses session Day/Month/Year fields, normalizes sessions to `yyyy/mm/dd`, and writes a mapping CSV (book identifier → `read_dates`).

  Implementation details for M5:
  - CLI entrypoints:
    * `--use-read-dates` (deprecated in the current codebase) — when present the extractor runs before enrichment.
    * `--limit N` — stop after collecting N books.
    * `--headless` — run in headless mode (optional; headful recommended for interactive login).
    * `--debug` / `--verbose` — print visited URLs, matched lines, and parsing decisions for troubleshooting.
  - Output format:
    * Cache CSV: `data/enriched/read_dates_cache.csv` with columns `book_key,read_dates` where `read_dates` is `START,END[;START,END]*`.
    * Extractor must be resilient to missing per-row `review/show` links; prefer visiting `review/show/<id>` when present.
  - Parsing policy:
    * Pair `Started` → `Finished` events in order of appearance; if a `Finished` appears without a preceding `Started`, skip that pair.
    * Treat `Shelved`/`Shelved as:` as metadata and only consider it if it appears in the absence of `Finished` as an optional end marker (configurable fallback).
    * Prefer the most recent finished session when merging into enrichment.

M6 | Integrate extractor into pipeline and enrichment
  - Add an optional extractor step in `run_pipeline.py` that runs before enrichment and merges extracted `read_dates` into the cleaned DataFrame.
  - Update `src/enrichment.py` to prefer `read_dates` when present and apply the SPEC fallbacks when `read_dates` are missing.

M7 | CLI flags, caching and Streamlit toggle
  - Add a `--use-read-dates` flag to `run_pipeline.py` and a Streamlit sidebar toggle to enable/skip extraction at runtime.
  - Implement simple caching for extracted results (CSV cache in `data/enriched/`) and a `--refresh` option to re-run extraction.

{{
M8 | Tests, validation and sample data
  - Add unit tests for the `read_dates` parser, enrichment fallbacks, and pages/time allocation algorithm.
  - Include a small sample `data/sample_raw_goodreads_export.csv` with representative cases (multiple sessions, single-date fallbacks, missing dates).

M9 | Documentation & contributor notes
  - Update `README.md` and `SPEC_Reading_Dashboard.md` with Playwright installation steps, how to run the extractor (headful login flow), expected runtime considerations, and troubleshooting tips.

M10 | Performance & UX improvements (optional)
  - Optimize extraction speed by reusing a single Playwright context/tab, add optional headless mode, and surface progress in the Streamlit UI when extraction runs.
  - Add rate-limiting and polite delays if the extractor causes site load issues.

}}
