"""Simple Playwright-based scraper to collect titles/authors from the user's 'read' shelf.

This is a diagnostic/test extractor: it does NOT compare to any CSV and simply
visits the Goodreads review list (shelf=read) pages and collects the title and
author from each row. It writes results to data/enriched/read_titles_scrape.csv
and returns the list of tuples.

Usage example (from repo root):
    python3 -m src.goodreads_title_scraper --limit 25 --max-pages 5

Note: Playwright must be installed and browsers set up:
    python3 -m pip install -r requirements.txt
    python3 -m playwright install
"""
from typing import List, Tuple, Optional
import time
import csv
from pathlib import Path
import re
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def _normalize_key(title: str, author: str) -> str:
    # same normalization used elsewhere: lowercase, strip punctuation, collapse spaces
    s = f"{title or ''} {author or ''}".lower()
    s = re.sub(r"[\"'`\[\]\(\){}:;,\.\?/\\|@#$%^&*_+=<>~<>-]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


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
    # Try weird variants like 'Jun 2026' with extra whitespace
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


def scrape_read_titles(limit: int = 0, headful: bool = True, debug: bool = False, delay: float = 1.0, max_pages: int = 0) -> List[Tuple[str, str, str]]:
    """Scrape titles and authors from the user's "read" shelf.

    Returns a list of tuples: (title, author, normalized_key)
    """
    out: List[Tuple[str, str, str]] = []
    if sync_playwright is None:
        raise RuntimeError("Playwright sync API not available. Please install playwright and run `playwright install`.")

    with sync_playwright() as p:
        if headful:
            print("Headful mode enabled: a browser window should open for Goodreads login.")
        else:
            print("Headless mode enabled: no visible browser window will open. Remove --headless to log in interactively.")
        browser = p.chromium.launch(headless=not headful)
        page = browser.new_page()
        review_list_url = "https://www.goodreads.com/review/list?shelf=read"
        page.goto(review_list_url)
        # Give the user instructions and then wait for confirmation. Make sure the user
        # logs in and navigates to their "My Books" list (read shelf) before pressing Enter.
        if headful:
            try:
                print("Please log into Goodreads in the opened browser and confirm you can see your 'My Books' list (read shelf). Press Enter when ready to continue.")
                input()
            except EOFError:
                print("No interactive input available; continuing without explicit confirmation.")

        # Quick diagnostic: confirm we are on a page that exposes book rows. If not,
        # wait briefly for the expected selector and print helpful debug info.
        try:
            # wait up to 10s for at least one book link to appear
            page.wait_for_selector("a.bookTitle", timeout=10000)
        except Exception:
            # nothing matched; print the current URL and a small snippet of the page
            print("DEBUG: No book links found after login. Current page:", page.url)
            snippet = page.content()[:2000]
            print("--- Start of page snippet ---\n" + snippet + "\n--- End of page snippet ---")
            # continue anyway so the caller sees the empty result; better to exit but keep consistent

        scraped = 0
        page_num = 0
        while True:
            page_num += 1
            if max_pages and page_num > max_pages:
                if debug:
                    print(f"Reached max_pages ({max_pages}); stopping before page {page_num}.")
                break

            rows = page.query_selector_all("table#booksBody tr")
            if not rows:
                rows = page.query_selector_all("tr.bookalike")
            if debug:
                print(f"Scanning page {page_num}, rows={len(rows)}")

            for r in rows:
                try:
                    # Prefer the list-page title and author cells: td.field.title a and td.field.author a
                    title_el = r.query_selector("td.field.title a") or r.query_selector("a.bookTitle")
                    author_el = r.query_selector("td.field.author a") or r.query_selector("a.authorName")
                    if not title_el:
                        # Debugging: write the row HTML to a snippets file to inspect structure
                        if debug:
                            try:
                                row_html = r.inner_html()
                            except Exception:
                                row_html = "<could not get inner_html>"
                            snippets_dir = Path("data/enriched/read_titles_row_snippets")
                            snippets_dir.mkdir(parents=True, exist_ok=True)
                            snippet_file = snippets_dir / f"page{page_num}_row{scraped+1}.html"
                            with snippet_file.open("w", encoding="utf8") as sf:
                                sf.write(row_html)
                            print(f"DEBUG: no title_el in row; wrote snippet to {snippet_file}")
                        continue
                    title = title_el.inner_text().strip()
                    author = author_el.inner_text().strip() if author_el else ""

                    # Try to extract date started/read directly from the list row (fast path)
                    ds_el = r.query_selector("td.field.date_started .date_started_value")
                    dr_el = r.query_selector("td.field.date_read .date_read_value")
                    raw_ds = ds_el.inner_text().strip() if ds_el else ""
                    raw_dr = dr_el.inner_text().strip() if dr_el else ""
                    # normalize to YYYY/MM/DD; if month-only like 'Jun 2026' -> use the 1st of month
                    date_started = _parse_date_str(raw_ds)
                    date_finished = _parse_date_str(raw_dr)

                    key = _normalize_key(title, author)
                    out.append((title, author, key, date_started, date_finished))
                    scraped += 1
                    if debug:
                        print(f"Found: {title} — {author} (key={key}) ds={date_started!r} dr={date_finished!r}")
                    if limit and scraped >= limit:
                        break
                except Exception as e:
                    if debug:
                        print("Row parse error:", e)
                    continue

            if limit and scraped >= limit:
                break

            # find "next" link to paginate
            next_el = None
            for a in page.query_selector_all("a"):
                try:
                    txt = a.inner_text().strip().lower()
                except Exception:
                    txt = ""
                if txt in ("next", "next ", "next >", "next »", ">", "»", "›"):
                    next_el = a
                    break
            if not next_el:
                if debug:
                    print("No next link found; finished pages.")
                break
            # if clicking Next would exceed max_pages, stop instead
            if max_pages and page_num >= max_pages:
                if debug:
                    print(f"Will not click Next because max_pages={max_pages} and already processed page {page_num}.")
                break
            try:
                next_el.click()
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(delay)
            except Exception as e:
                if debug:
                    print("Failed to click Next:", e)
                break

        browser.close()

    # write results to CSV for inspection
    out_path = Path("data/enriched/read_titles_scrape.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["title", "author", "key", "date_started", "date_finished"])
        writer.writeheader()
        for row in out:
            # row is (title, author, key, date_started, date_read) per the scraper
            t, a, k, ds, dr = row
            writer.writerow({"title": t, "author": a, "key": k, "date_started": ds, "date_finished": dr})

    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max number of titles to scrape (0 = unlimited)")
    parser.add_argument("--page-limit", "--max-pages", dest="max_pages", type=int, default=0, help="Max number of pages to visit (0 = unlimited)")
    parser.add_argument("--headful", dest="headful", action="store_true", help="Run browsers in headful mode (interactive login)")
    parser.add_argument("--headless", dest="headful", action="store_false", help="Run browsers in headless mode")
    parser.set_defaults(headful=True)
    parser.add_argument("--debug", action="store_true", help="Verbose debug output")
    parser.add_argument("--delay", type=float, default=1.0, help="Polite delay between page actions (seconds)")
    args = parser.parse_args()

    results = scrape_read_titles(limit=args.limit, headful=args.headful, debug=args.debug, delay=args.delay, max_pages=args.max_pages)
    print(f"Scraped {len(results)} titles. Wrote data/enriched/read_titles_scrape.csv")
