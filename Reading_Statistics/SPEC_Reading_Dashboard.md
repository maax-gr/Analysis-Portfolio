# Reading Statistics Dashboard: Project Spec

Comments are indicated as `{{ comment }}` and are not subject of the current implementation. Ignore while working on the code. Comments can also span multiple lines.

## 1. Overview

**Purpose:** 
- Build a Dashboard that shows my reading statistics
- I want to see how many books and pages I have read recently
- I want to see some statistics about which types of books I enjoy most (authors, genres, etc.)

**Primary user(s):** 
- me
- would be nice to have the dashboard accessible through github, so I can show it to people

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
- The dashboard must enter an idle/locked state while the scraper runs in the background and refresh after the extraction finishes and the cache is merged into the enriched CSV.
- The extraction step is an offline pipeline step. It is not executed by the main dashboard rendering loop.
- Conservative delays are required to avoid rate issues or page-load problems: default is `1.0s` between navigations.

## 3. Repository Structure

data/
raw_goodreads_library_export.csv            # Goodreads export (gitignored)
enriched_goodreads_library_export.csv       # output of enrichment
read_dates_cache.csv                        # intermediate scraper cache
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
- Use the first/most recent valid date pair per book, depending on the page data, and store it in `data/read_dates_cache.csv`.
- Support smoke tests with a `--page-limit` / `--max-pages` option and a default `--delay` of `1.0s`.
- Do not require terminal confirmation before continuing after page load; the user can log in in the visible browser window and the script continues automatically.

Scraper output:
- Final cache file: `data/read_dates_cache.csv`
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
  * `Date Started` = scraped value when available; otherwise fallback to `Date Added`, capped at `Date Finished` when the book was added after it was finished.
  * `Date Finished` = scraped value when available; otherwise fallback to `Date Read`.
- Preserve an explicit `Date Read` even when it precedes `Date Added`. If it is
  missing, use `Date Added` as the fallback for book-based statistics.
- This ensures the dashboard and KPI logic can rely on the date columns existing on every rebuild, even before the extractor runs.
- The final enrichment stage merges the extracted dates into the cleaned data and writes the result to the enriched CSV.

### 4.5 Dashboard integration
The dashboard must read from the enriched CSV for its metrics and visualizations.

Requirements:
- Launching the dashboard should show the metrics already available from the current enriched data.
- If the enriched file is missing, create it from raw data without online lookups.
- Compare read-shelf Book IDs in raw data with the IDs in enriched data and
  warn if they differ. Do not silently overwrite an existing stale file.
- A sidebar button named `Extract reading dates from Goodreads` opens a confirmation popup (`Are you sure?`) with `Yes` and `No`.
- Pressing `Yes` starts the scraper in the background.
- Pressing `No` aborts and returns to the current dashboard state.
- A sidebar button named `Re-run from raw data` also opens the same confirmation popup and only proceeds on `Yes`.
- The button is disabled while the scraper is already running.
- After extraction completes, the dashboard reruns the pipeline and refreshes the view to reflect the newly merged dates.
- This refresh uses the cache file `data/read_dates_cache.csv` and merges it into the raw read-data output.
- Re-running from raw recalculates statistics without running the Goodreads
  scraper or online genre lookups. Preserve existing dates and genre metadata
  where possible, and reuse exact matches in the read-dates cache.
- A genre lookup button below the reading-date button confirms and runs a
  background lookup for all read books or only books with empty `genre_raw`,
  or cancels. Display the current book number and total while the dashboard is locked.

### 4.6 Additional stats to calculate
- Days until finished: number of days between `Date Started` and `Date Finished`
- Average pages read per day: `Number of Pages` / `Days until finished`
- If `Number of Pages` is missing or `Days until finished` is not positive, leave the value null.
- Calculate per-day page totals across the relevant range using the derived reading window for each book.
- Filter book-based statistics by `Date Read`; pages over time are allocated to
  calendar days in the reading interval, including intervals crossing years.

### 4.7 Security & etiquette notes
- Treat the extractor as a personal automation tool.
- Do not commit credentials or cookies.
- Use a visible browser window for Goodreads login; headless mode is not supported.
- Keep delays conservative and operate only on the user's own Goodreads data.

{{ 
Additional columns (Column | Type | Description ):
* genre_raw | JSON list[str] | Original categories/subjects from the API
* genre | str | Mapped to one of my broad genres (see 5.3); null/NA if no reliable match
* lookup_status | str | `matched` / `not_found` / `error`
* genre_source | str | Source of newly matched subjects, if known }}


## 5. Genre Enrichment

### 5.1 Sources & order of attempts
1. Open Library by valid ISBN-13 (or ISBN-10 normalized to ISBN-13), then title + author; treat its subjects as raw genres.
2. Fall back to Google Books by ISBN, then title + author, if Open Library finds no subjects.
3. No manual override file for now; if no genre is found, leave `genre` as null/NA and `lookup_status` as `not_found`.

### 5.2 Behaviour
- Missing mode checks whether `genre_raw` has subjects, independently of status.
  All-book mode refreshes every read book. Within a run, cache results by lookup key.
- Search by the title without a colon-delimited subtitle or trailing parenthesized
  or bracketed details. Allow a leading "The" to differ, while requiring an
  exact normalized author match; prefer exact full-title matches.
- Collect all raw subjects/genres returned by the API/source, not just the first match; we will refine the mapping rule later.
- Wait at least 1.1 seconds before each request attempt, including retries,
  to stay below Open Library's default one-request-per-second limit.
- Retry transient request failures once and stop after three consecutive books
  for which Open Library fails without a successful response.
- Map each new result immediately and atomically checkpoint each processed book.
  Stop without overwriting if the enriched CSV changes concurrently.
- No match leaves `genre = null` and `lookup_status = not_found`. Report request
  errors separately as `lookup_status = error`, retaining previous genre data.
- After a Google Books HTTP 429, skip Google for the rest of the run. Books
  without an Open Library match remain errors and are retried on a later run.
- Record the source for new matches. Older cached matches may have an unknown source.
- `None` should never be treated as `Other`; `Other` is only used when a non-empty subject list exists but no category matches.
- Missing mode skips books with saved subjects; all-book mode rechecks them.
- API keys: read from environment variables / `.env` (never committed). Initial implementation may use a public Google Books request without a key when allowed; if a key is needed later, it must be configured via env.
- The lookup should use the same normalization helpers as the rest of the project to avoid ISBN/title-author mismatches due to punctuation or formatting.

### 5.3 Genre mapping
> Map messy raw categories to a small, fixed set. One primary genre per book.
> We collect all available subject strings and then apply a deterministic rule order: the first matching category wins.

| My genre | Raw terms that map to it (case-insensitive contains) |
|---|---|
| Historical Fiction | historical fiction, fiction historical, historical novel |
| Fantasy | fantasy, epic fantasy, urban fantasy, magic, wizard, dragons, elf, hobbit, mythology, mythic, quest, fairy tale, sorcery |
| Crime / Mystery | detective, mystery, thriller, crime, noir, police, spy |
| Science Fiction | science fiction, sci fi, sci-fi, speculative fiction, space opera |
| Literary Fiction | literary fiction, contemporary fiction, classic literature, literature |
| Non-fiction: History | history, historical, military history, world history |
| Non-fiction: Science | science, nature, astronomy, biology, physics, technology, medicine |
| Self-help / Psychology | psychology, self help, motivation, thought and thinking, conduct of life, happiness, behavior modification, personal growth, sociology, interpersonal relations |
| Biography / Memoir | biography, memoir, autobiography, personal narrative, travel, travelogue, hiking, outdoor, adventure, essay, essays |
| Other | fallback when a non-empty subject list exists but no rule matches |

**Conflict rule when several match:** first match in the table order wins. Matches use whole words or phrases, not fragments inside words. If no category matches and there is at least one raw subject, use `Other`; if there are no raw subjects, leave `genre` as null. Existing matched subjects are remapped without online requests.


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
3. Pages vs Rating
  * Scatter plot
  * x-axis: `My Rating`
  * y-axis: `Number of Pages`
  * takes global filter into account
  * The plot is square (1:1 aspect ratio), occupies roughly half the screen width, and leaves the adjacent space empty for future plots.
  * A checkbox `Limit pages axis to 1000` restricts the y-axis to 0..1000 and hides any books above that threshold from the visible range (without removing them from the underlying data set).

### 6.5 Layout & style
- single page to begin with (might be modified when further charts are added)
- KPI section should occupy no more than 25% of available space at the top
- Theme & colors: tbd. Start with grayscale
- Chart titles on top of chart. Centered around the middle of each graph. Axis titles centered around middle of axis. 
 - Chart layout: two main charts should be presented side-by-side in the same row
   - Left: `Books read per month` (bar chart)
   - Right: `Pages read over time` (line chart)
 - `Pages vs Rating` scatter plot should be placed below the two main charts (full-width for now)
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
    * `--use-read-dates` — fuzzy-match the existing cache without running the extractor.
    * `--refresh-read-dates` — explicitly run the extractor before enrichment.
    * `--limit N` — stop after collecting N books.
    * no `--headless` flag — the scraper runs in a visible browser window for login and automation.
    * `--debug` / `--verbose` — print visited URLs, matched lines, and parsing decisions for troubleshooting.
  - Output format:
    * Cache CSV: `data/read_dates_cache.csv` with columns `title,author,key,date_started,date_finished`.
    * Extractor must be resilient to missing per-row `review/show` links; prefer visiting `review/show/<id>` when present.
  - Parsing policy:
    * Pair `Started` → `Finished` events in order of appearance; if a `Finished` appears without a preceding `Started`, skip that pair.
    * Treat `Shelved`/`Shelved as:` as metadata and only consider it if it appears in the absence of `Finished` as an optional end marker (configurable fallback).
    * Prefer the most recent finished session when merging into enrichment.

M6 | Integrate extractor into pipeline and enrichment
  - Add an optional extractor step in `run_pipeline.py` that runs before enrichment and merges extracted `read_dates` into the cleaned DataFrame.
  - Update `src/enrichment.py` to prefer `read_dates` when present and apply the SPEC fallbacks when `read_dates` are missing.

M7 | CLI flags, caching and Streamlit toggle
  - Use `--use-read-dates` to match the existing cache and the Streamlit extraction button to run the scraper.
  - Use the CSV cache in `data/` and `--refresh-read-dates` to re-run extraction explicitly.

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
