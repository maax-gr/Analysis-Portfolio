"""Enrichment utilities (genre lookup, caching) for the Reading Dashboard.

For M2 we implement a minimal enrichment step that computes the derived
columns described in the spec (Days until finished, average pages/day) and
writes an enriched CSV. External API lookups (genre mapping) remain TODO and
are left commented in the code for future milestones.
"""
from typing import Any, Optional
import re
from difflib import SequenceMatcher

import pandas as pd




def _strip_wrapping_quotes(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    s = s.replace("\ufeff", "")
    s = s.strip('"\'“”‘’`')
    return s


def _normalize_text(value: Any) -> str:
    s = _strip_wrapping_quotes(value)
    s = s.lower()
    s = s.replace("&", " and ")
    s = s.replace("’", "'")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _reverse_author_name(value: Any) -> str:
    original = _strip_wrapping_quotes(value)
    if not original or "," not in original:
        return _normalize_text(value)
    first, second = [part.strip() for part in original.split(",", 1)]
    if not first or not second:
        return _normalize_text(value)
    return _normalize_text(f"{second} {first}")


def _normalize_title_author(title: Any, author: Any) -> str:
    return f"{_normalize_text(title)} {_normalize_text(author)}".strip()


def _title_author_candidates(title: Any, author: Any):
    title_norm = _normalize_text(title)
    author_norm = _normalize_text(author)
    author_rev = _reverse_author_name(author)
    candidates = {f"{title_norm} {author_norm}".strip()}
    if author_norm:
        candidates.add(f"{title_norm} {author_rev}".strip())
    if title_norm:
        candidates.add(title_norm)
    return {c for c in candidates if c}


def _match_ratio(left: Any, right: Any) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _normalize_text(left), _normalize_text(right)).ratio()


def compute_enrichment(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived columns and return enriched DataFrame.

    Adds:
    - `Date Started` and `Date Finished` columns whenever they are missing
    - `Days until finished` (int) = days between Date Started and Date Finished
    - `average pages read per day` (float) = Number of Pages / Days until finished

    Rules implemented per spec:
    - if Number of Pages is null -> average pages/day = NaN
    - if Days until finished == 0 -> average pages/day = NaN
    - if scraped dates are missing, fall back to Date Added / Date Read
    """
    df = df.copy()

    for col in ["Date Started", "Date Finished"]:
        if col not in df.columns:
            df[col] = pd.NaT

    if "Date Added" in df.columns:
        df["Date Started"] = pd.to_datetime(df["Date Started"], errors="coerce")
        df["Date Started"] = df["Date Started"].combine_first(pd.to_datetime(df["Date Added"], errors="coerce"))

    if "Date Read" in df.columns:
        df["Date Finished"] = pd.to_datetime(df["Date Finished"], errors="coerce")
        df["Date Finished"] = df["Date Finished"].combine_first(pd.to_datetime(df["Date Read"], errors="coerce"))

    start_col = "Date Started"
    end_col = "Date Finished"

    df["Days until finished"] = (df[end_col] - df[start_col]).dt.days
    df.loc[df["Days until finished"].isna(), "Days until finished"] = pd.NA
    df["Days until finished"] = df["Days until finished"].astype("Int64")

    def _avg_pages(row: pd.Series) -> Optional[float]:
        pages = row.get("Number of Pages")
        days = row.get("Days until finished")
        if pd.isna(pages) or pd.isna(days):
            return pd.NA
        if int(days) == 0:
            return pd.NA
        return float(pages) / float(int(days))

    df["average pages read per day"] = df.apply(_avg_pages, axis=1)
    return df


def match_scraped_titles_to_raw(df: pd.DataFrame, scraped_df: pd.DataFrame) -> pd.DataFrame:
    """Match scraped Goodreads titles/authors to the raw library export.

    We keep exact normalized matches as the primary path, but also allow a fuzzy
    fallback for titles/authors that differ only by quote stripping, punctuation,
    or the common Lastname, Firstname vs Firstname Lastname ordering used by Goodreads.
    """
    if scraped_df is None or scraped_df.empty:
        return df

    df = df.copy()
    if "Date Started" not in df.columns:
        df["Date Started"] = pd.NaT
    if "Date Finished" not in df.columns:
        df["Date Finished"] = pd.NaT

    scraped_records = []
    for _, row in scraped_df.iterrows():
        title = row.get("title") or row.get("Title") or ""
        author = row.get("author") or row.get("Author") or ""
        title_norm = _normalize_text(title)
        author_norm = _normalize_text(author)
        author_rev = _reverse_author_name(author)
        record = {
            "title": title,
            "author": author,
            "title_norm": title_norm,
            "author_norm": author_norm,
            "author_rev": author_rev,
            "title_author_keys": _title_author_candidates(title, author),
            "date_started": row.get("date_started") or row.get("Date Started") or "",
            "date_finished": row.get("date_finished") or row.get("Date Finished") or "",
        }
        scraped_records.append(record)

    for idx, row in df.iterrows():
        raw_title = row.get("Title") or ""
        raw_author = row.get("Author") or ""
        raw_title_norm = _normalize_text(raw_title)
        raw_author_norm = _normalize_text(raw_author)
        raw_author_rev = _reverse_author_name(raw_author)
        raw_keys = _title_author_candidates(raw_title, raw_author)

        best_match = None
        best_score = 0.0

        for rec in scraped_records:
            if not rec["title_author_keys"]:
                continue
            key_overlap = bool(raw_keys & rec["title_author_keys"])
            if key_overlap:
                score = 1.0
            else:
                title_score = _match_ratio(raw_title, rec["title"])
                author_score = max(
                    _match_ratio(raw_author, rec["author"]),
                    _match_ratio(raw_author, rec["author_rev"]),
                    _match_ratio(raw_author_rev, rec["author"]),
                    _match_ratio(raw_author_norm, rec["author_norm"]),
                    _match_ratio(raw_author_rev, rec["author_rev"]),
                )
                score = 0.7 * title_score + 0.3 * author_score
                if raw_title_norm and rec["title_norm"] and raw_title_norm in rec["title_norm"]:
                    score = max(score, 0.96)
                if rec["title_norm"] and raw_title_norm and rec["title_norm"] in raw_title_norm:
                    score = max(score, 0.96)
                if raw_title_norm == rec["title_norm"] and author_score >= 0.7:
                    score = max(score, 0.98)

            if score > best_score:
                best_score = score
                best_match = rec

        if best_match is None:
            continue

        if best_score < 0.82:
            continue

        start_val = best_match["date_started"]
        end_val = best_match["date_finished"]

        if start_val:
            start_dt = pd.to_datetime(start_val, format="%Y/%m/%d", errors="coerce")
            if pd.notna(start_dt):
                df.at[idx, "Date Started"] = start_dt
        if end_val:
            end_dt = pd.to_datetime(end_val, format="%Y/%m/%d", errors="coerce")
            if pd.notna(end_dt):
                df.at[idx, "Date Finished"] = end_dt

        if pd.isna(df.at[idx, "Date Started"]) and pd.notna(row.get("Date Added")):
            df.at[idx, "Date Started"] = pd.to_datetime(row.get("Date Added"), errors="coerce")
        if pd.isna(df.at[idx, "Date Finished"]) and pd.notna(row.get("Date Read")):
            df.at[idx, "Date Finished"] = pd.to_datetime(row.get("Date Read"), errors="coerce")

    return df


def merge_read_dates_into_df(df: pd.DataFrame, cache_map=None) -> pd.DataFrame:
    """Merge a cache_map of read dates into the cleaned DataFrame.

    `cache_map` is a mapping book_key -> (date_started, date_finished) where
    `book_key` is the normalized Title+Author string (per SPEC). This function
    will set `Date Started` and `Date Finished` for rows that have matching
    cache entries. Only a single most-recent session is expected per book.
    """
    if not cache_map:
        return df

    df = df.copy()

    def _book_key_from_row(row: pd.Series) -> str:
        return _normalize_title_author(row.get("Title"), row.get("Author"))

    if "Date Started" not in df.columns:
        df["Date Started"] = pd.NaT
    if "Date Finished" not in df.columns:
        df["Date Finished"] = pd.NaT

    for idx, row in df.iterrows():
        key = _book_key_from_row(row)
        entry = cache_map.get(key)
        if not entry:
            continue
        start_s, end_s = entry
        try:
            start_dt = pd.to_datetime(start_s, format="%Y/%m/%d", errors="coerce")
            end_dt = pd.to_datetime(end_s, format="%Y/%m/%d", errors="coerce")
        except Exception:
            continue
        if pd.isna(start_dt) or pd.isna(end_dt):
            continue
        if pd.notna(row.get("Date Added")) and end_dt < row.get("Date Added"):
            end_dt = row.get("Date Added")
        df.at[idx, "Date Started"] = start_dt
        df.at[idx, "Date Finished"] = end_dt

    return df
