"""Playwright extractor: visit Goodreads read-shelf rows and per-row view pages.

The extractor intentionally scrapes every visible book on the user's read shelf,
records the title and author, opens each book's `/review/show/...` page, parses
"Reading process", and stores the result in `data/enriched/read_dates_cache.csv`
and `data/enriched/read_titles_scrape.csv`.
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
    s = re.sub(r"[\"'`\[\]\(\){}:;,.\?/\\|@#$%^&*_+=<>~<>-]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_reading_process(text: str) -> Optional[tuple]:
    found = re.findall(
        r"([A-Za-z]+ \d{1,2}, \d{4})\s*[–—-]\s*(Started(?: Reading)?|Finished(?: Reading)?|Finished)\b",
        text,
        flags=re.IGNORECASE,
    )
    sessions = []
    for date_s, action in found:
        dt = None
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                dt = datetime.strptime(date_s, fmt)
                break
            except Exception:
                continue
        if dt is not None:
            sessions.append((dt, action.lower()))

    paired = []
    start = None
    for dt, action in sessions:
        if "start" in action:
            start = dt
        elif "finish" in action:
            if start is not None:
                paired.append((start, dt))
                start = None

    if not paired:
        return None
    paired.sort(key=lambda x: x[1], reverse=True)
    latest = paired[0]
    return latest[0].strftime("%Y/%m/%d"), latest[1].strftime("%Y/%m/%d")


def _parse_date_str(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y/%m/%d")
        except Exception:
            pass
    for fmt in ("%B %Y", "%b %Y"):
        try:
            return datetime.strptime(s, fmt).replace(day=1).strftime("%Y/%m/%d")
        except Exception:
            pass
    m = re.match(r"([A-Za-z]+)\s+(\d{4})", s)
    if m:
        mon, yr = m.group(1), m.group(2)
        for fmt in ("%b %Y", "%B %Y"):
            try:
                return datetime.strptime(f"{mon} {yr}", fmt).replace(day=1).strftime("%Y/%m/%d")
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


def extract_read_dates(
    book_keys: Iterable[str],
    cache_path: Optional[str] = None,
    headful: bool = True,
    debug: bool = False,
    limit: int = 0,
    refresh: bool = False,
    delay: float = 1.0,
    page_limit: int = 0,
) -> Dict[str, tuple]:
    """Scrape every visible title on the Goodreads read shelf and return a map.

    The old behavior filtered rows against a predetermined set of `book_keys`.
    The required behavior is broader: every read-shelf book visible on the page is
    collected, the matching is performed later against the raw CSV, and the cache
    is written using the normalized `Title + Author` key.
    """
    cache_map = load_cache(cache_path) if cache_path else {}
    if sync_playwright is None:
        return cache_map

    scraped_rows = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        page = browser.new_page()
        review_list_url = "https://www.goodreads.com/review/list?shelf=read"
        page.goto(review_list_url)
        print("Opening Goodreads read shelf. If in headful mode, log in if needed.")
        try:
            page.wait_for_selector("td.field.title a, a.bookTitle", timeout=120000)
        except Exception:
            try:
                print(
                    "Could not detect read-shelf rows automatically. If the browser is visible, ensure the list is on the 'read' shelf and press Enter to continue."
                )
                input()
            except Exception:
                print("No interactive input available; continuing without explicit confirmation.")

        scraped_count = 0
        page_num = 0
        while True:
            page_num += 1
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
                    title_el = r.query_selector("td.field.title a") or r.query_selector("a.bookTitle")
                    author_el = r.query_selector("td.field.author a") or r.query_selector("a.authorName")
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()
                    author = author_el.inner_text().strip() if author_el else ""
                    key = _normalize_key(title, author)
                    if not key:
                        continue
                    if key in seen:
                        continue
                    seen.add(key)

                    parsed_ds = ""
                    parsed_dr = ""
                    ds_el = r.query_selector("td.field.date_started .date_started_value")
                    dr_el = r.query_selector("td.field.date_read .date_read_value")
                    if ds_el:
                        parsed_ds = _parse_date_str(ds_el.inner_text().strip())
                    if dr_el:
                        parsed_dr = _parse_date_str(dr_el.inner_text().strip())

                    link_el = r.query_selector("a[href*='/review/show/']")
                    if link_el:
                        try:
                            book_view = page.evaluate("el => el.href", link_el)
                        except Exception:
                            href = link_el.get_attribute("href")
                            book_view = href if href and href.startswith("http") else f"https://www.goodreads.com{href}"
                        if debug:
                            print(f"Visiting {book_view} for key={key}")
                        page.goto(book_view)
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
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
                            parsed_ds, parsed_dr = parsed
                    elif debug:
                        print(f"No review/show link for {key}; continuing without view-page parse.")

                    record = {"title": title, "author": author, "date_started": parsed_ds, "date_finished": parsed_dr}
                    scraped_rows.append(record)
                    cache_map[key] = (parsed_ds, parsed_dr)
                    scraped_count += 1
                    if debug:
                        print(f"Scraped {key}: ds={parsed_ds!r} dr={parsed_dr!r}")

                    if limit and scraped_count >= limit:
                        break
                except Exception as e:
                    if debug:
                        print("Row processing error", e)
                    continue

            if limit and scraped_count >= limit:
                break

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
            if page_limit and page_num >= page_limit:
                if debug:
                    print(f"Will not click Next because page_limit={page_limit} and already processed page {page_num}.")
                break
            try:
                next_el.click()
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(delay)
            except Exception:
                break

        browser.close()

    if cache_path:
        write_cache(cache_path, cache_map)

    scraped_path = (Path(cache_path).parent / "read_titles_scrape.csv") if cache_path else Path("data/enriched/read_titles_scrape.csv")
    scraped_path.parent.mkdir(parents=True, exist_ok=True)
    with scraped_path.open("w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["title", "author", "date_started", "date_finished"])
        writer.writeheader()
        for row in scraped_rows:
            writer.writerow({
                "title": row["title"],
                "author": row["author"],
                "date_started": row["date_started"],
                "date_finished": row["date_finished"],
            })

    return cache_map
