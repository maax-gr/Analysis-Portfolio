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
* dashboard framework: Streamlit
* charts: Plotly/Altair/Matplotlib
* scraping: Playwright
- Compatibility with GitHub: the project is intended to run locally and in GitHub-hosted/portable environments without hardcoded secrets.

Implementation constraints:
- The Goodreads extractor is intentionally headful only: it opens a visible browser window for login and scraping. `--headless` is not supported because Goodreads sign-in is interactive and headless auth is unreliable.
- The scraper starts automatically when the user triggers it from the dashboard; it does not wait for a terminal prompt.
- The dashboard must stay responsive while the scraper runs in the background and refresh after the extraction finishes and the cache is merged into the enriched CSV.
- The extraction step is an offline pipeline step. It is not executed by the main dashboard rendering loop.
- Conservative delays are required to avoid rate issues or page-load problems: default is `1.0s` between navigations.

## 3. Repository Structure

data/
raw_goodreads_library_export.csv            # Goodreads export (gitignored)
enriched_goodreads_library_export.csv       # output of enrichment
enriched/
  read_dates_cache.csv                      # intermediate scraper cache
notebooks/         # exploration only
src/
cleaning.py        # load + clean Goodreads CSV
enrichment.py      # matching + enrichment logic
metrics.py         # aggregation functions for charts
goodreads_title_scraper.py  # headful Goodreads read-shelf scraper
goodreads_playwright.py     # compatibility/extraction helper scripts
Reading_Dashboard.py
run_pipeline.py
SPEC_Reading_Dashboard.md
README.md

## 4. Data

### 4.1 Input: Goodreads export
The raw Goodreads export is the authoritative list of books and metadata.

- Only rows on the `read` shelf are kept for final stats.
- The raw CSV is not modified; the pipeline creates the enriched output at `data/enriched_goodreads_library_export.csv`.
- The raw file may include quotes around values such as title/author. These are normalized during matching and cleaning.

Canonical match key:
- Build a `book_key` as `normalized_title + " " + normalized_author`.
- Normalization includes lowercasing, stripping quotation marks, removing punctuation, and collapsing repeated whitespace.
- Matching uses the same logic in both scraper and pipeline to avoid drift between the raw export and the extracted read-shelf content.

### 4.2 Goodreads Scraper

Entry point:
- `https://www.goodreads.com/review/list?shelf=read`

Responsibilities:
- Open the read shelf directly and scrape all visible books on each page.
- Save each visible `title` and `author` encountered on the shelf.
- For each book, visit the per-row review view page when available and parse the "Reading process" block for `Started Reading` and `Finished Reading` dates.
- Use the first/most recent valid date pair per book, depending on the page data, and store it in `data/enriched/read_dates_cache.csv`.
- Support smoke tests with a `--page-limit` / `--max-pages` option and a default `--delay` of `1.0s`.
- Do not require terminal confirmation before continuing after page load; the user can log in in the visible browser window and the script continues automatically.

Scraper output:
- Final cache file: `data/enriched/read_dates_cache.csv`
- Columns: `title, author, key, date_started, date_finished`
- `key` is the normalized `Title + Author` key used by the enrichment layer.

Examples of accepted data in the Goodreads reading history:
- `September 23, 2026 – Started Reading`
- `September 28, 2026 – Finished Reading`
- `January 9, 2023 – Shelved`
- `February 1, 2026 – Started Reading`
- `February 11, 2026 – Finished Reading`

Parsing rules:
- Accept date text such as `MonthName DD, YYYY` and `MonthName D, YYYY`.
- Ignore `Shelved` events as session boundaries unless the event is clearly a reading-state marker.
- Normalize dates to `YYYY/MM/DD`.
- Keep only the most recent valid finished session for the cache entry when multiple reading sessions are present.

Page navigation:
- Visit each row's view page before moving to the next page.
- Click the `next` pagination link until no next link remains or `--page-limit` / `--max-pages` is reached.

### 4.3 Matching logic (after extraction)
The matching step runs after the scraper completes and writes the merged data into the enriched CSV.

Requirements:
- Build the canonical matching key for each row as normalized `Title + Author`.
- Strip quotes, punctuation, and extra whitespace before comparison.
- Prefer exact normalized `Title + Author` matches.
- If exact matching fails, apply a fuzzy fallback using similarity/substring matching on the normalized title and author values.
- Do not rely on review IDs as the match key.
- When a match succeeds, copy `date_started` and `date_finished` into the raw row and keep the old Date Read / Date Added as fallback values only if no scraper date exists.

This is deliberately more forgiving than a strict exact match because Goodreads titles and authors often differ by quotation marks, punctuation, or small formatting variations.

### 4.4 Enriched output
File: `data/enriched_goodreads_library_export.csv`

Rules:
- Keep only books where `Exclusive Shelf == "read"`.
- Remove other shelf states such as `to-read` or `currently-reading`.
- The enriched CSV always contains the columns `Date Started` and `Date Finished`, even before any scraper match has been applied.
- Populate those columns as follows:
  * `Date Started` = scraped value when available; otherwise fallback to `Date Added`.
  * `Date Finished` = scraped value when available; otherwise fallback to `Date Read`.
- This ensures the dashboard and KPI logic can rely on the date columns existing on every rebuild, even before the extractor runs.
- The final enrichment stage merges the extracted dates into the cleaned data and writes the result to the enriched CSV.

### 4.5 Dashboard integration
The dashboard must read from the enriched CSV for its metrics and visualizations.

Requirements:
- Launching the dashboard should show the metrics already available from the current enriched data.
- A sidebar button named `Extract reading dates from Goodreads` starts the scraper in the background.
- The button is disabled while the scraper is already running.
- After extraction completes, the dashboard reruns the pipeline and refreshes the view to reflect the newly merged dates.
- This refresh uses the cache file `data/enriched/read_dates_cache.csv` and merges it into the raw read-data output.

### 4.6 Additional stats to calculate
- Days until finished: number of days between `Date Started` and `Date Finished`
- Average pages read per day: `Number of Pages` / `Days until finished`
- If `Number of Pages` is missing or `Days until finished` is zero, leave the value null.
- Calculate per-day page totals across the relevant range using the derived reading window for each book.

### 4.7 Security & etiquette notes
- Treat the extractor as a personal automation tool.
- Do not commit credentials or cookies.
- Use a visible browser window for Goodreads login; headless mode is not supported.
- Keep delays conservative and operate only on the user's own Goodreads data.

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
    * no `--headless` flag — the scraper runs in a visible browser window for login and automation.
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
  - Optimize extraction speed by reusing a single Playwright context/tab, keep the browser visible for Goodreads sign-in, and surface progress in the Streamlit UI when extraction runs.
  - Add rate-limiting and polite delays if the extractor causes site load issues.

}}
