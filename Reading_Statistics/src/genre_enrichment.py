"""Standalone genre enrichment helpers for Goodreads books.

The API lookup layer is intentionally pure and side-effect free: it only fetches
book metadata if requested, normalizes subjects into a common list format, and
maps those subjects to a small set of broad genres.
"""
from __future__ import annotations

import json
import hashlib
import math
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib import error, parse, request

import pandas as pd


REQUEST_DELAY_SECONDS = 1.1
MAX_CONSECUTIVE_PROVIDER_FAILURES = 3


@dataclass
class LookupState:
    google_rate_limited: bool = False
    open_library_failures: int = 0


GENRE_RULES: List[tuple[str, List[str]]] = [
    ("Historical Fiction", ["historical fiction", "fiction historical", "historical novel", "historical novels"]),
    ("Fantasy", [
        "fantasy", "epic fantasy", "urban fantasy", "magic", "wizard", "wizards",
        "dragon", "dragons", "elf", "elves", "hobbit", "hobbits", "mythology",
        "mythic", "quest", "fairy tale", "fairy tales", "sorcery", "legendary"
    ]),
    ("Crime / Mystery", ["detective", "mystery", "thriller", "crime", "noir", "police", "spy"]),
    ("Science Fiction", ["science fiction", "sci fi", "sci-fi", "speculative fiction", "space opera"]),
    ("Literary Fiction", ["literary fiction", "contemporary fiction", "classic literature", "literature"]),
    ("Non-fiction: History", ["history", "military history", "world history"]),
    ("Non-fiction: Science", ["science", "nature", "astronomy", "biology", "physics", "technology", "medicine"]),
    ("Self-help / Psychology", [
        "psychology", "self help", "self-help", "motivation", "thought and thinking",
        "conduct of life", "happiness", "behavior modification", "personal growth",
        "self actualization", "success in business", "productivity", "organizational behavior",
        "business", "management", "interpersonal relations", "social psychology", "sociology"
    ]),
    ("Biography / Memoir", [
        "biography", "memoir", "autobiography", "personal narrative", "travel", "travelogue",
        "hiking", "outdoor", "adventure", "essay", "essays", "description and travel"
    ]),
]


def _normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _short_title(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    title = str(value).strip().split(":", 1)[0].strip()
    return re.sub(r"\s*(?:\([^()]*\)|\[[^\[\]]*\])\s*$", "", title).strip()


def _title_key(value: Any) -> str:
    title = _normalize_text(_short_title(value))
    return re.sub(r"^the\s+", "", title)


def _titles_match(left: Any, right: Any) -> bool:
    left_key, right_key = _title_key(left), _title_key(right)
    return bool(left_key and right_key and left_key == right_key)


def _normalize_isbn(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isfinite(float(value)):
            value = str(int(float(value)))

    text = str(value).strip()
    if not text:
        return ""

    # Handle quoted and floating forms from CSV/Excel exports such as
    # `="9781407247427"` or `9781407247427.0`.
    text = text.replace("=\"", "").replace("\"", "")
    text = text.strip("'")
    if text.lower().endswith(".0"):
        text = text[:-2]

    cleaned = re.sub(r"[^0-9xX]", "", text)
    if len(cleaned) == 10 and cleaned[:9].isdigit() and (cleaned[-1].isdigit() or cleaned[-1].lower() == "x"):
        check10 = 10 if cleaned[-1].lower() == "x" else int(cleaned[-1])
        if (sum(int(digit) * (10 - i) for i, digit in enumerate(cleaned[:9])) + check10) % 11:
            return ""
        digits = "978" + cleaned[:9]
        check = (10 - sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(digits)) % 10) % 10
        return digits + str(check)
    if len(cleaned) == 13 and cleaned.isdigit():
        if sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(cleaned)) % 10 == 0:
            return cleaned
    return ""


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        original = str(item).strip()
        clean = _normalize_text(original)
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(original)
    return result


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [v for v in value]
    return [str(value)]


def _extract_subjects_from_google_volume(volume: Dict[str, Any]) -> List[str]:
    if not isinstance(volume, dict):
        return []
    info = volume.get("volumeInfo", {})
    raw_subjects: List[str] = []
    for key in ("categories", "subjects", "genre", "genres"):
        raw_subjects.extend(_coerce_list(info.get(key)))
    return _dedupe(raw_subjects)


def _extract_subjects_from_open_library(doc: Dict[str, Any]) -> List[str]:
    if not isinstance(doc, dict):
        return []
    raw_subjects: List[str] = []
    for key in ("subject", "subjects", "subject_facet", "genres"):
        raw_subjects.extend(_coerce_list(doc.get(key)))
    if "works" in doc and isinstance(doc["works"], list):
        for work in doc["works"]:
            if isinstance(work, dict):
                raw_subjects.extend(_coerce_list(work.get("subjects")))
    return _dedupe(raw_subjects)


def _fetch_json(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    for attempt in range(2):
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            req = request.Request(url, headers={"User-Agent": "Reading Statistics Dashboard/0.1 (personal use)"})
            with request.urlopen(req, timeout=timeout) as resp:
                payload = resp.read().decode("utf-8")
                return json.loads(payload)
        except error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt or exc.code not in (500, 502, 503, 504):
                raise
        except (error.URLError, TimeoutError):
            if attempt:
                raise
    raise RuntimeError("Request retry loop ended unexpectedly")


def _google_books_lookup_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    if not isbn:
        return None
    query = parse.quote(f"isbn:{isbn}")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=5"
    return _fetch_json(url)


def _google_books_lookup_by_title_author(title: str, author: str) -> Optional[Dict[str, Any]]:
    title_q = _normalize_text(_short_title(title))
    author_q = _normalize_text(author)
    if not title_q or not author_q:
        return None
    query = parse.quote(f"intitle:{title_q} inauthor:{author_q}")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=5"
    return _fetch_json(url)


def _open_library_lookup_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    if not isbn:
        return None

    edition_url = f"https://openlibrary.org/isbn/{isbn}.json"
    edition_data = _fetch_json(edition_url)
    if isinstance(edition_data, dict):
        subjects = _extract_subjects_from_open_library(edition_data)
        work_refs = edition_data.get("works") or []
        for work in work_refs:
            if not isinstance(work, dict):
                continue
            key = work.get("key")
            if not key:
                continue
            work_url = f"https://openlibrary.org{key}.json"
            work_data = _fetch_json(work_url)
            if isinstance(work_data, dict):
                subjects.extend(_extract_subjects_from_open_library(work_data))
        if subjects:
            return {"subjects": _dedupe(subjects)}

    query = parse.quote(isbn)
    url = f"https://openlibrary.org/search.json?q={query}&limit=5"
    data = _fetch_json(url)
    if not isinstance(data, dict):
        return None
    docs = data.get("docs") or []
    if not docs:
        return None
    subjects = []
    for doc in docs:
        if isinstance(doc, dict) and isbn in [_normalize_isbn(value) for value in _coerce_list(doc.get("isbn"))]:
            subjects.extend(_extract_subjects_from_open_library(doc))
    return {"subjects": _dedupe(subjects)} if subjects else None


def _open_library_lookup_by_title_author(title: str, author: str) -> Optional[Dict[str, Any]]:
    title_q = _normalize_text(_short_title(title))
    author_q = _normalize_text(author)
    if not title_q or not author_q:
        return None
    query = parse.urlencode({"title": title_q, "author": author_q, "limit": 10,
                             "fields": "key,title,author_name,subject"})
    url = f"https://openlibrary.org/search.json?{query}"
    data = _fetch_json(url)
    if not isinstance(data, dict):
        return None
    docs = data.get("docs") or []
    docs = sorted(docs, key=lambda doc: (
        not isinstance(doc, dict) or _normalize_text(doc.get("title")) != _normalize_text(title)
    ))
    for doc in docs:
        if isinstance(doc, dict):
            title_matches = _titles_match(doc.get("title"), title)
            author_candidates = _coerce_list(doc.get("author_name"))
            author_matches = any(_normalize_text(candidate) == author_q for candidate in author_candidates)
            if title_matches and author_matches:
                if _extract_subjects_from_open_library(doc):
                    return doc
                key = doc.get("key")
                if isinstance(key, str) and key.startswith("/works/"):
                    work_data = _fetch_json(f"https://openlibrary.org{key}.json")
                    if isinstance(work_data, dict) and _extract_subjects_from_open_library(work_data):
                        return work_data
    return None


def map_subjects_to_genre(raw_subjects: Iterable[str]) -> Optional[str]:
    """Map one or many raw subject strings to a broad genre bucket.

    Rules:
    - a non-empty subject list with no known terms remains `Other`
    - an empty or null subject list stays `None`
    - this function intentionally does not turn `None` into `Other`
    """
    subjects = [str(item).strip() for item in raw_subjects if str(item).strip()]
    if not subjects:
        return None
    normalized_subjects = [_normalize_text(s) for s in subjects]
    for genre_name, keywords in GENRE_RULES:
        for term in normalized_subjects:
            for keyword in keywords:
                pattern = r"(?<!\w)" + re.escape(_normalize_text(keyword)) + r"(?!\w)"
                if re.search(pattern, term):
                    return genre_name
    return "Other"


def _build_genre_result(raw_subjects: List[str], source: Optional[str]) -> Dict[str, Any]:
    clean_subjects = _dedupe(raw_subjects)
    if not clean_subjects:
        return {
            "genre_raw": [],
            "genre": None,
            "lookup_status": "not_found",
            "source": source,
        }
    genre = map_subjects_to_genre(clean_subjects)
    return {
        "genre_raw": clean_subjects,
        "genre": genre,
        "lookup_status": "matched",
        "source": source,
    }


def remap_saved_genres(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate categories from saved raw subjects without network requests."""
    out = df.copy()
    if "genre_raw" not in out.columns:
        return out
    if "genre" not in out.columns:
        out["genre"] = None
    out["genre"] = out["genre"].astype(object)
    for idx, row in out.iterrows():
        status = row.get("lookup_status")
        if not isinstance(status, str) or status != "matched":
            continue
        raw = row["genre_raw"]
        if pd.isna(raw) or not str(raw).strip():
            continue
        try:
            subjects = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid genre_raw JSON for Book Id {row.get('Book Id', idx)}") from exc
        if not isinstance(subjects, list) or not all(isinstance(item, str) for item in subjects):
            raise ValueError(f"Expected genre_raw to be a list of strings for Book Id {row.get('Book Id', idx)}")
        out.at[idx, "genre"] = map_subjects_to_genre(subjects)
    return out


def _google_subjects(data: Any, title: str, author: str, isbn: str = "") -> List[str]:
    if not isinstance(data, dict):
        return []
    subjects: List[str] = []
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        info = item.get("volumeInfo") or {}
        identifiers = info.get("industryIdentifiers") or []
        isbns = {_normalize_isbn(value.get("identifier")) for value in identifiers if isinstance(value, dict)}
        title_matches = _titles_match(info.get("title"), title)
        authors = _coerce_list(info.get("authors"))
        author_matches = any(_normalize_text(value) == _normalize_text(author) for value in authors)
        if (isbn and isbn in isbns) or (title and author and title_matches and author_matches):
            subjects.extend(_extract_subjects_from_google_volume(item))
    return _dedupe(subjects)


def lookup_genre_for_book(
    title: Any,
    author: Any,
    isbn: Any = None,
    cache: Optional[Dict[str, Dict[str, Any]]] = None,
    include_open_library: bool = True,
    state: Optional[LookupState] = None,
) -> Dict[str, Any]:
    """Look up subjects in Open Library first, with Google Books as fallback.

    The function intentionally keeps the raw subject list and returns None instead
    of "Other" when there is no raw data to map.
    """
    isbn_norm = _normalize_isbn(isbn)
    cache_key = isbn_norm or f"{_normalize_text(title)}|{_normalize_text(author)}"
    if cache is not None and cache_key in cache:
        return cache[cache_key]

    if state is None:
        state = LookupState()
    attempts = []
    if include_open_library and isbn_norm:
        attempts.append(("open_library_isbn", lambda: _extract_subjects_from_open_library(
            _open_library_lookup_by_isbn(isbn_norm))))
    if include_open_library and _normalize_text(title) and _normalize_text(author):
        attempts.append(("open_library_title_author", lambda: _extract_subjects_from_open_library(
            _open_library_lookup_by_title_author(title, author))))
    if isbn_norm:
        attempts.append(("google_books_isbn", lambda: _google_subjects(
            _google_books_lookup_by_isbn(isbn_norm), title, author, isbn_norm)))
    if _normalize_text(title) and _normalize_text(author):
        attempts.append(("google_books_title_author", lambda: _google_subjects(
            _google_books_lookup_by_title_author(title, author), title, author)))

    errors = []
    open_failed = False
    open_succeeded = False
    result = _build_genre_result([], None)
    for source, fetch in attempts:
        if source.startswith("google_books_") and state.google_rate_limited:
            if not errors:
                errors.append("Google Books was skipped after an earlier rate-limit response")
            continue
        try:
            subjects = fetch()
            if source.startswith("open_library_"):
                open_succeeded = True
        except error.HTTPError as exc:
            errors.append(f"{source}: {exc}")
            if source.startswith("open_library_"):
                open_failed = True
            if source.startswith("google_books_") and exc.code == 429:
                state.google_rate_limited = True
            continue
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append(f"{source}: {exc}")
            if source.startswith("open_library_"):
                open_failed = True
            continue
        if subjects:
            result = _build_genre_result(subjects, source)
            break
    if open_succeeded:
        state.open_library_failures = 0
    elif open_failed:
        state.open_library_failures += 1
    if errors:
        print(f"Genre lookup errors for {title}: {'; '.join(errors)}", file=sys.stderr)
        if result["lookup_status"] == "not_found":
            result["lookup_status"] = "error"
    if cache is not None and result["lookup_status"] != "error":
        cache[cache_key] = result
    return result


def has_raw_genres(value: Any) -> bool:
    if value is None or pd.isna(value) or not str(value).strip():
        return False
    try:
        subjects = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid genre_raw JSON") from exc
    if not isinstance(subjects, list) or not all(isinstance(item, str) for item in subjects):
        raise ValueError("genre_raw must be a JSON list of strings")
    return any(item.strip() for item in subjects)


def enrich_dataframe_genres(
    df: pd.DataFrame,
    cache: Optional[Dict[str, Dict[str, Any]]] = None,
    include_open_library: bool = True,
    mode: str = "missing",
    checkpoint: Optional[Callable[[pd.DataFrame], None]] = None,
    progress: Optional[Callable[[int, int, int], None]] = None,
) -> pd.DataFrame:
    """Look up read-shelf books, saving each completed row when requested."""
    if mode not in ("all", "missing"):
        raise ValueError(f"Unknown genre lookup mode: {mode}")
    out = df.copy()
    if "genre_raw" not in out.columns:
        out["genre_raw"] = None
    if "genre" not in out.columns:
        out["genre"] = None
    if "lookup_status" not in out.columns:
        out["lookup_status"] = None
    if "genre_source" not in out.columns:
        out["genre_source"] = None
    for column in ("genre_raw", "genre", "lookup_status", "genre_source"):
        out[column] = out[column].astype(object)

    selected = []
    for idx, row in out.iterrows():
        if str(row.get("Exclusive Shelf", "")).strip().lower() != "read":
            continue
        try:
            filled = has_raw_genres(row["genre_raw"])
        except ValueError as exc:
            raise ValueError(f"Invalid genre_raw for Book Id {row.get('Book Id', idx)}: {exc}") from exc
        if mode == "all" or not filled:
            selected.append(idx)

    state = LookupState()
    total = len(selected)
    if progress:
        progress(0, total, 0)
    for completed, idx in enumerate(selected):
        row = out.loc[idx]
        if progress:
            progress(completed, total, completed + 1)

        isbn = next((value for value in (row.get("ISBN13"), row.get("ISBN"))
                     if pd.notna(value) and _normalize_isbn(value)), None)
        result = lookup_genre_for_book(
            row.get("Title"),
            row.get("Author"),
            isbn,
            cache=cache,
            include_open_library=include_open_library,
            state=state,
        )
        if result["lookup_status"] == "not_found" and has_raw_genres(row["genre_raw"]):
            print(f"No new genres found for {row.get('Title')}; keeping existing genres.", file=sys.stderr)
        if result["lookup_status"] == "matched" or (
                result["lookup_status"] == "not_found" and not has_raw_genres(row["genre_raw"])):
            out.at[idx, "genre_raw"] = json.dumps(result["genre_raw"], ensure_ascii=False)
            out.at[idx, "genre"] = result["genre"]
            out.at[idx, "genre_source"] = result.get("source")
        if result["lookup_status"] == "matched" or not has_raw_genres(row["genre_raw"]):
            out.at[idx, "lookup_status"] = result["lookup_status"]
        if checkpoint:
            checkpoint(out)
        if progress:
            progress(completed + 1, total, 0)
        if state.open_library_failures >= MAX_CONSECUTIVE_PROVIDER_FAILURES:
            raise RuntimeError(
                "Open Library failed for three consecutive books. "
                "Saved results are safe; retry missing books later."
            )
    return out


def write_enriched_file(path: Path, result: pd.DataFrame, original_digest: bytes) -> bytes:
    """Atomically save results unless the source changed during processing."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            result.to_csv(handle, index=False)
        if hashlib.sha256(path.read_bytes()).digest() != original_digest:
            raise RuntimeError(f"{path} changed during genre processing; results were not saved")
        new_digest = hashlib.sha256(temp_path.read_bytes()).digest()
        os.replace(temp_path, path)
        return new_digest
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def enrich_genres_file(path: Path, remap_only: bool = False, mode: str = "missing",
                       progress: Optional[Callable[[int, int, int], None]] = None) -> pd.DataFrame:
    """Update an existing enriched CSV after all requested operations finish."""
    digest = hashlib.sha256(path.read_bytes()).digest()
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"Book Id", "Title", "Author", "Exclusive Shelf"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {', '.join(sorted(missing))}")
    def save_checkpoint(result: pd.DataFrame) -> None:
        nonlocal digest
        digest = write_enriched_file(path, result, digest)

    if remap_only:
        result = remap_saved_genres(df)
        save_checkpoint(result)
        return result
    return enrich_dataframe_genres(df, cache={}, mode=mode, checkpoint=save_checkpoint, progress=progress)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Look up genres for all enriched books.")
    parser.add_argument("enriched_csv", type=Path)
    parser.add_argument("--remap-only", action="store_true", help="Remap saved subjects without online lookups")
    parser.add_argument("--mode", choices=("all", "missing"), default="missing")
    parser.add_argument("--progress-file", type=Path)
    args = parser.parse_args()
    def report(completed: int, total: int, current: int) -> None:
        if args.progress_file:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.progress_file.parent,
                                             delete=False) as handle:
                temporary = Path(handle.name)
                try:
                    json.dump({"completed": completed, "total": total, "current": current}, handle)
                except (OSError, ValueError):
                    temporary.unlink(missing_ok=True)
                    raise
            try:
                os.replace(temporary, args.progress_file)
            finally:
                temporary.unlink(missing_ok=True)

    df = enrich_genres_file(args.enriched_csv, remap_only=args.remap_only, mode=args.mode, progress=report)
    if args.remap_only:
        print("Remapped saved genre subjects without online lookups.")
        return
    attempted = df.loc[df["Exclusive Shelf"].str.strip().str.lower().eq("read")]
    errors = int(attempted["lookup_status"].eq("error").sum())
    matched = int(attempted["lookup_status"].eq("matched").sum())
    not_found = int(attempted["lookup_status"].eq("not_found").sum())
    print(f"Genre lookup finished for {len(attempted)} books: "
          f"{matched} matched, {not_found} not found, {errors} errors.")


if __name__ == "__main__":
    main()
