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
- Compatability with GitHub

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
  * Number of Pages | int | nothing
  * Year Published | int | nothing
  * Original Publication Year | int | nothing
  * Date Read | date yyyy/mm/dd | nothing 
  * Date Added | date yyyy/mm/dd | nothing
  * Exclusive Shelf | str | nothing
  * My Review | str | strip `"` if present 

Books with missing dates: 
- set "Date Read" == "Date Added" (whichever one exists determines the date)
- if both are missing -> set Null and ignore in all algorithms

If "Date Read" < "Date Added"
- set "Date Read" == "Date Added"

All other fields:
- if empty: set to null 

Which books count in the stats?
- books with 'Exclusive Shelf == "read"'




### 4.2 Enriched output
**File:** `data/enriched_goodreads_library_export.csv`
Additional columns (Column | Type | Description ):
* Days until finished | int | counting the days between "Date Added" and "Date Read"
* average pages read per day | float | "Number of Pages"/"Days until finished"
  - if Number of pages is missing -> set to Null
  - if "Days until finished" = 0 ('Date Read' == 'Date Added') -> set to Null

### 4.3 Additional stats to calculate
"pages read on day":
  * Calculate for every day between min date added (from entire book list) and current date, how many pages were read
    - algorithm example: iterate through each day, check if there are any books with date_added <= iteration_day AND date_read >= iteration_day, add "average pages read per day" to "pages read on day"
  * only use books where "average pages read per day" is not Null
  

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
M3 | Dashboard v1: KPIs, Charts 1 & 2; fixed filter to "This Year"; no possiblilty to change filter at this stage
M4 | Dashboard v2: add functional filter as described
M5 | conceptiualize further functions (genre mapping, pulling date started instead of date added etc.)
