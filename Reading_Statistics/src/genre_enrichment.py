"""Standalone genre enrichment helpers for Goodreads books.

The API lookup layer is intentionally pure and side-effect free: it only fetches
book metadata if requested, normalizes subjects into a common list format, and
maps those subjects to a small set of broad genres.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib import parse, request


GENRE_RULES: List[tuple[str, List[str]]] = [
    ("Crime / Mystery", ["detective", "mystery", "thriller", "crime", "noir", "police", "spy"]),
    ("Science Fiction", ["science fiction", "sci fi", "sci-fi", "speculative fiction", "space opera", "space"]),
    ("Fantasy", [
        "fantasy", "epic fantasy", "urban fantasy", "magic", "wizard", "wizards",
        "dragon", "dragons", "elf", "elves", "hobbit", "hobbits", "mythology",
        "mythic", "quest", "fairy tale", "fairy tales", "sorcery", "legendary"
    ]),
    ("Literary Fiction", ["literary fiction", "contemporary fiction", "classic literature", "literature"]),
    ("Non-fiction: History", ["history", "historical", "military history", "world history"]),
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
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _normalize_isbn(value: Any) -> str:
    if value is None:
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
    if len(cleaned) == 10 and cleaned[-1].lower() == "x":
        return cleaned
    if len(cleaned) == 13:
        return cleaned
    return ""


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        clean = _normalize_text(item)
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
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
    try:
        req = request.Request(url, headers={"User-Agent": "Reading Statistics Dashboard/0.1 (personal use)"})
        with request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)
    except Exception:
        return None


def _google_books_lookup_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    if not isbn:
        return None
    query = parse.quote(f"isbn:{isbn}")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=5"
    return _fetch_json(url)


def _google_books_lookup_by_title_author(title: str, author: str) -> Optional[Dict[str, Any]]:
    title_q = _normalize_text(title)
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
        if _extract_subjects_from_open_library(edition_data):
            return edition_data
        work_refs = edition_data.get("works") or []
        for work in work_refs:
            if not isinstance(work, dict):
                continue
            key = work.get("key")
            if not key:
                continue
            work_url = f"https://openlibrary.org{key}.json"
            work_data = _fetch_json(work_url)
            if isinstance(work_data, dict) and _extract_subjects_from_open_library(work_data):
                return work_data

    query = parse.quote(isbn)
    url = f"https://openlibrary.org/search.json?q={query}&limit=5"
    data = _fetch_json(url)
    if not isinstance(data, dict):
        return None
    docs = data.get("docs") or []
    if not docs:
        return None
    for doc in docs:
        if isinstance(doc, dict) and _extract_subjects_from_open_library(doc):
            return doc
    return docs[0]


def _open_library_lookup_by_title_author(title: str, author: str) -> Optional[Dict[str, Any]]:
    title_q = _normalize_text(title)
    author_q = _normalize_text(author)
    if not title_q or not author_q:
        return None
    query = parse.quote(f"{title_q} {author_q}")
    url = f"https://openlibrary.org/search.json?q={query}&limit=5"
    data = _fetch_json(url)
    if not isinstance(data, dict):
        return None
    docs = data.get("docs") or []
    for doc in docs:
        if isinstance(doc, dict):
            title_matches = _normalize_text(doc.get("title")) == title_q
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
                return doc
    return docs[0] if docs else None


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
                if keyword in term:
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


def lookup_genre_for_book(
    title: Any,
    author: Any,
    isbn: Any = None,
    cache: Optional[Dict[str, Dict[str, Any]]] = None,
    include_open_library: bool = True,
) -> Dict[str, Any]:
    """Lookup a broad genre for a book using ISBN first, then title/author fallback.

    The function intentionally keeps the raw subject list and returns None instead
    of "Other" when there is no raw data to map.
    """
    isbn_norm = _normalize_isbn(isbn)
    cache_key = isbn_norm or f"{_normalize_text(title)}|{_normalize_text(author)}"
    if cache is not None and cache_key in cache:
        return cache[cache_key]

    raw_subjects: List[str] = []
    source: Optional[str] = None

    if isbn_norm:
        google_data = _google_books_lookup_by_isbn(isbn_norm)
        if isinstance(google_data, dict):
            raw_subjects = _extract_subjects_from_google_volume(google_data.get("items", [{}])[0])
            if raw_subjects:
                source = "google_books_isbn"
        if not raw_subjects and include_open_library:
            open_data = _open_library_lookup_by_isbn(isbn_norm)
            if isinstance(open_data, dict):
                raw_subjects = _extract_subjects_from_open_library(open_data)
                if raw_subjects:
                    source = "open_library_isbn"

    if not raw_subjects:
        title_q = _normalize_text(title)
        author_q = _normalize_text(author)
        if title_q and author_q:
            google_data = _google_books_lookup_by_title_author(title_q, author_q)
            if isinstance(google_data, dict):
                items = google_data.get("items") or []
                for item in items:
                    candidates = _extract_subjects_from_google_volume(item)
                    if candidates:
                        raw_subjects = candidates
                        source = "google_books_title_author"
                        break
            if not raw_subjects and include_open_library:
                open_data = _open_library_lookup_by_title_author(title_q, author_q)
                if isinstance(open_data, dict):
                    raw_subjects = _extract_subjects_from_open_library(open_data)
                    if raw_subjects:
                        source = "open_library_title_author"

    result = _build_genre_result(raw_subjects, source)
    if cache is not None:
        cache[cache_key] = result
    return result


def enrich_dataframe_genres(
    df: Any,
    cache: Optional[Dict[str, Dict[str, Any]]] = None,
    include_open_library: bool = True,
) -> Any:
    """Attach genre metadata to a DataFrame while preserving all original data."""
    out = df.copy()
    if "genre_raw" not in out.columns:
        out["genre_raw"] = None
    if "genre" not in out.columns:
        out["genre"] = None
    if "lookup_status" not in out.columns:
        out["lookup_status"] = None

    for idx, row in out.iterrows():
        shelf = str(row.get("Exclusive Shelf") or "").strip().lower()
        if shelf and shelf != "read":
            out.at[idx, "genre_raw"] = []
            out.at[idx, "genre"] = None
            out.at[idx, "lookup_status"] = "not_found"
            continue

        result = lookup_genre_for_book(
            row.get("Title"),
            row.get("Author"),
            row.get("ISBN13") or row.get("ISBN"),
            cache=cache,
            include_open_library=include_open_library,
        )
        out.at[idx, "genre_raw"] = result.get("genre_raw")
        out.at[idx, "genre"] = result.get("genre")
        out.at[idx, "lookup_status"] = result.get("lookup_status")
    return out
