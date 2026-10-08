"""Playwright extractor: visit Goodreads review list and per-row view pages.

Behavior follows SPEC: use normalized `Title + Author` as `book_key`, visit
each row's `/review/show/<id>` view page on the list, parse the "Reading
process" block, and store a single most-recent finished session per book in
`data/enriched/read_dates_cache.csv` as `book_key,date_started,date_finished`.
"""
from typing import Dict, Iterable, Optional
import csv
import re
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def _normalize_key(title: str, author: str) -> str:
    s = f"{title or ''} {author or ''}".lower()
    # strip punctuation, collapse whitespace, trim
    s = re.sub(r"[\"'`\[\]\(\){}:;,\.\?/\\|@#$%^&*_+=<>~<>-]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_reading_process(text: str) -> Optional[tuple]:
    # find all (date, action) occurrences
    found = re.findall(r"([A-Za-z]+ \d{1,2}, \d{4})\s*[–—-]\s*(Started(?: Reading)?|Finished(?: Reading)?|Finished)\b", text, flags=re.IGNORECASE)
    sessions = []
    for date_s, action in found:
        dt = None
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                dt = datetime.strptime(date_s, fmt)
                break
            except Exception:
                continue
        if dt is None:
            continue
        sessions.append((dt, action.lower()))

    # pair start -> finish
    paired = []
    start = None
    for dt, action in sessions:
        if "start" in action:
            start = dt
        elif "finish" in action:
            if start:
                paired.append((start, dt))
                start = None

    if not paired:
        return None
    # return most recent by finish date
    paired.sort(key=lambda x: x[1], reverse=True)
    latest = paired[0]
    return latest[0].strftime("%Y/%m/%d"), latest[1].strftime("%Y/%m/%d")


def _parse_date_str(s: str) -> str:
    """Parse a date string from Goodreads list row and return YYYY/MM/DD.

    Accepts formats like:
      - 'June 30, 2026' or 'Jun 30, 2026'
      - 'June 2026' or 'Jun 2026' (no day) -> returns first day of month
    Returns empty string on failure.
    """
    if not s:
        return ""
    s = s.strip()
    # Try full month day, year formats
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y/%m/%d")
        except Exception:
            pass
    # Try month + year only (no day) -> assume first day of month
    for fmt in ("%B %Y", "%b %Y"):
        try:
            dt = datetime.strptime(s, fmt)
            # set day to 1
            dt = dt.replace(day=1)
            return dt.strftime("%Y/%m/%d")
        except Exception:
            pass
    # Try simple regex like 'Jun 2026'
    m = re.match(r"([A-Za-z]+)\s+(\d{4})", s)
    if m:
        mon, yr = m.group(1), m.group(2)
        try:
            dt = datetime.strptime(f"{mon} {yr}", "%b %Y")
            dt = dt.replace(day=1)
            return dt.strftime("%Y/%m/%d")
        except Exception:
            try:
                dt = datetime.strptime(f"{mon} {yr}", "%B %Y")
                dt = dt.replace(day=1)
                return dt.strftime("%Y/%m/%d")
            except Exception:
                pass
    return ""


def load_cache(cache_path: str) -> Dict[str, tuple]:
    p = Path(cache_path)
    out = {}
    if not p.exists():
        return out
    with p.open("r", newline="", encoding="utf8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            k = r.get("book_key")
            ds = r.get("date_started")
            df = r.get("date_finished")
            if k:
                out[k] = (ds or "", df or "")
    return out


def write_cache(cache_path: str, cache_map: Dict[str, tuple]):
    p = Path(cache_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["book_key", "date_started", "date_finished"])
        writer.writeheader()
        for k, v in cache_map.items():
            writer.writerow({"book_key": k, "date_started": v[0] or "", "date_finished": v[1] or ""})


def extract_read_dates(book_keys: Iterable[str], cache_path: Optional[str] = None, headful: bool = True, debug: bool = False, limit: int = 0, refresh: bool = False, delay: float = 0.6, page_limit: int = 0) -> Dict[str, tuple]:
    """Extract read dates and return map book_key -> (date_started, date_finished).

    - `book_keys`: iterable of normalized Title+Author keys to consider.
    - `cache_path`: path to CSV cache. If provided, load and update it.
    - `refresh`: if True, re-scrape even if cache entry exists.
    """
    keys = list(book_keys)
    cache_map = load_cache(cache_path) if cache_path else {}

    # Determine which keys need scraping
    to_scrape = []
    for k in keys:
        existing = cache_map.get(k)
        if refresh:
            to_scrape.append(k)
        else:
            if not existing or not existing[0] or not existing[1]:
                to_scrape.append(k)

    if not to_scrape:
        return cache_map

    if sync_playwright is None:
        # Playwright not available; return current cache_map
        return cache_map

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        page = browser.new_page()
        review_list_url = "https://www.goodreads.com/review/list"
        page.goto(review_list_url)
        print("Opening review list. If a browser window is visible, please log into Goodreads and navigate to your 'My Books' (read shelf).")
        # Try to wait for the book rows to appear automatically (no stdin needed).
        try:
            page.wait_for_selector("td.field.title a, a.bookTitle", timeout=120000)
        except Exception:
            # If we can't detect the list rows within the timeout, fall back to asking
            # the user to confirm via Enter when stdin is available. If stdin is not
            # connected (EOFError), proceed and let the extractor handle the missing rows.
            try:
                print("Could not detect book rows automatically. If the browser is visible, navigate to your 'My Books' list and press Enter to continue.")
                input()
            except Exception:
                print("No interactive input available; proceeding without explicit confirmation.")

        scraped = 0
        page_num = 0
        while True:
            # page_num is the number of the page we're about to process (start at 1)
            page_num += 1
            # If a page limit was provided, stop before processing pages beyond it.
            # page_limit=5 -> process pages 1..5 and then stop without clicking Next.
            if page_limit and page_num > page_limit:
                if debug:
                    print(f"Reached page limit ({page_limit}); stopping before page {page_num}.")
                break
            rows = page.query_selector_all("table#booksBody tr")
            if not rows:
                rows = page.query_selector_all("tr.bookalike")
            if debug:
                print(f"Scanning page {page_num}, rows={len(rows)}")

            for r in rows:
                try:
                    # read title and author
                    title_el = r.query_selector("a.bookTitle")
                    author_el = r.query_selector("a.authorName")
                    if not title_el:
                        continue
                    title = title_el.inner_text().strip()
                    author = author_el.inner_text().strip() if author_el else ""
                    candidate = _normalize_key(title, author)
                    if debug:
                        print(f"Row candidate='{candidate}' ; need_scrape={'yes' if candidate in to_scrape else 'no'}")
                    if candidate not in to_scrape:
                        continue

                    # First attempt: extract dates directly from the list row if present
                    ds_el = r.query_selector("td.field.date_started .date_started_value")
                    dr_el = r.query_selector("td.field.date_read .date_read_value")
                    raw_ds = ds_el.inner_text().strip() if ds_el else ""
                    raw_dr = dr_el.inner_text().strip() if dr_el else ""
                    parsed_ds = _parse_date_str(raw_ds)
                    parsed_dr = _parse_date_str(raw_dr)
                    if parsed_ds or parsed_dr:
                        # Use whichever parsed values are present; if one missing, keep empty
                        existing = cache_map.get(candidate)
                        if refresh or not existing or not existing[0] or not existing[1]:
                            cache_map[candidate] = (parsed_ds, parsed_dr)
                            if debug:
                                print(f"Row-level dates for {candidate}: ds={parsed_ds!r} dr={parsed_dr!r}")
                    else:
                        # fallback: try visiting the /review/show/ page and parse reading_process
                        link_el = r.query_selector("a[href*='/review/show/']")
                        if not link_el:
                            if debug:
                                print(f"No review/show link for {candidate}; skipping view visit.")
                        else:
                            try:
                                book_view = page.evaluate("el => el.href", link_el)
                            except Exception:
                                href = link_el.get_attribute("href")
                                book_view = href if href and href.startswith("http") else f"https://goodreads.com{href}"
                            if debug:
                                print(f"Visiting {book_view} for key={candidate}")
                            page.goto(book_view)
                            time.sleep(delay)

                            content = ""
                            if page.query_selector("#reading_process"):
                                content = page.inner_text("#reading_process")
                            elif page.query_selector(".readingProcess"):
                                content = page.inner_text(".readingProcess")
                            else:
                                content = page.inner_text("body")

                            parsed = _parse_reading_process(content)
                            if parsed:
                                existing = cache_map.get(candidate)
                                if refresh or not existing or not existing[0] or not existing[1]:
                                    cache_map[candidate] = parsed
                                    if debug:
                                        print(f"Parsed for {candidate}: {parsed}")
                            else:
                                if debug:
                                    snippet = (content or "")[:800]
                                    print(f"No parse for {candidate}; snippet:\n{snippet}\n---")

                    scraped += 1
                    if limit and scraped >= limit:
                        break
                except Exception as e:
                    if debug:
                        print("Row processing error", e)
                    continue

            if limit and scraped >= limit:
                break

            # find next
            next_el = None
            for a in page.query_selector_all("a"):
                try:
                    txt = a.inner_text().strip().lower()
                except Exception:
                    txt = ""
                if txt in ("next", "next >", "next »", ">", "»", "›"):
                    next_el = a
                    break
            if not next_el:
                break
            # If page_limit would be exceeded by clicking next, then stop instead of clicking.
            if page_limit and page_num >= page_limit:
                if debug:
                    print(f"Will not click Next because page_limit={page_limit} and already processed page {page_num}.")
                break
            try:
                next_el.click()
                time.sleep(delay)
            except Exception:
                break

        browser.close()

    # write cache back
    if cache_path:
        write_cache(cache_path, cache_map)

    return cache_map
