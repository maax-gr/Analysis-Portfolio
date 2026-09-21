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
    * Dashboard framework: define together (Streamlit / Dash / other); must be possible to open in GitHub online
    * charts: define together (matplotlib, plotly, altair)
- Compatability with GitHub

**Constraints:**
- The dashboard reads only from `data/enriched/books.csv` and makes **no API calls at runtime**.
- Must run when executing the .py file
- charts must update while running .py file

## 3. Repository Structure

data/
  raw_goodreads_library_export/            # Goodreads export (gitignored)
  enriched_goodreads_library_export/       # output of enrichment step
notebooks/        # exploration only
src/
  cleaning.py     # load + clean Goodreads CSV
  enrichment.py   # genre lookup + caching
  genres.py       # genre mapping rules
  metrics.py      # aggregation functions used by charts
Reading_Dashboard.py            # dashboard entry point
SPEC_Reading_Dashboard.md
README.md

## 4. Data

### 4.1 Input: Goodreads export
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
  * Number of Pages | str | nothing
  * Year Published | int | nothing
  * Original Publication Year | int | nothing
  * Date Read | date | nothing 
  * Date Added | date | nothing
  * Exclusive Shelf | str | nothing
  * My Review | str | strip `"` if present 
- if empty: set to null 


**Which books count in the stats?** 
- books with 'Exclusive Shelf == "read"'

**Books with missing dates:** 
- set '"Date Read" == "Date Added"'


{{ ### 4.2 Enriched output
**File:** `data/enriched/books.csv`

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
    * Option "This Year" (shows all data from current year; derive from current date)
    * Option "Last Year" (shows all data from Previous year; derive from current year - 1)
    * Option "Last 3 Months" (shows all data from last 90 days; derive from current date)

{{ - [ ] Genre (multi-select)
- [ ] Rating (range)
- [ ] TODO }}

### 6.2 KPI cards (top row)
- Books read
- Total pages read
- Average rating
- Average pages per book
Show all stats for filtered range

### 6.3 Charts
1. Books Read per month
  * aggregate on date read
  * Bar chart. time on x-axis, number of books on y-axis. One bar per month.
  * takes global filter into account
2. Pages read over time
  * Calculated new column "Days until finished" by counting the days between "Date Added" and "Date Read". Calculate new column "average pages read per day" by "Number of Pages"/"Days until finished". 
  * Line Chart. Time Series on x-axis, accumulate



### 6.5 Layout & style
- Page layout: TODO (wide, tabs vs. single scroll page)
- Theme / colour palette: TODO
- Chart titles, axis labels and hover text required on all charts.
- Empty-state behaviour: TODO (e.g. show "No data for this filter" instead of an error)

## 7. Code Standards (for Copilot)
- Type hints on all functions; short docstrings.
- Pure functions in `src/` (no Streamlit/UI imports); `app.py` only handles layout and calls `src/`.
- Aggregation logic lives in `src/metrics.py` -> Question: Is that necessary? Can it not b determined on the fly?
- No hard-coded file paths in functions; use a config constant or argument.
- Prefer small functions 


## 10. Milestones

| Milestone | Deliverable | Done when |
|---|---|---|
| M1 | Repo setup, create and write README | App starts with a "hello" page |
| M2 | Cleaning module + tests | Clean DataFrame loads from raw CSV |
| M3 | Enrichment script + cache | `books.csv` produced, unmatched logged |
| M4 | Dashboard v1 (KPIs + 3 charts) | Runs locally with filters |
| M5 | Remaining charts + polish | All items in 6.3 done |
| M6 | Deployment + docs | Live link in README |
