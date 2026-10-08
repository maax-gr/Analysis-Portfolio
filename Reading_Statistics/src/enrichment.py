"""Enrichment utilities (genre lookup, caching) for the Reading Dashboard.

For M2 we implement a minimal enrichment step that computes the derived
columns described in the spec (Days until finished, average pages/day) and
writes an enriched CSV. External API lookups (genre mapping) remain TODO and
are left commented in the code for future milestones.
"""
from typing import Any, Optional
import pandas as pd
import numpy as np


def compute_enrichment(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived columns and return enriched DataFrame.

    Adds:
    - `Days until finished` (int) = days between Date Added and Date Read
    - `average pages read per day` (float) = Number of Pages / Days until finished

    Rules implemented per spec:
    - if Number of Pages is null -> average pages/day = NaN
    - if Days until finished == 0 -> average pages/day = NaN
    """
    df = df.copy()

    # Support the new SPEC fields: `Date Started` and `Date Finished` may be
    # present (added by the pipeline merging `read_dates`). If not present
    # fall back to the previous Date Added / Date Read behavior.
    if "Date Started" in df.columns and "Date Finished" in df.columns:
        start_col = "Date Started"
        end_col = "Date Finished"
    else:
        start_col = "Date Added"
        end_col = "Date Read"

    # Compute inclusive days between start and finish
    df["Days until finished"] = (df[end_col] - df[start_col]).dt.days
    # If either date is missing, result will be NaN
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
        title = row.get("Title") or ""
        author = row.get("Author") or ""
        # replicate normalization used by extractor
        s = f"{title} {author}".lower()
        s = re.sub(r"[\"'`\[\]\(\){}:;,\.\?/\\|@#$%^&*_+=<>~<>-]+", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    import re
    # prepare columns
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
        # enforce finish >= Date Added per SPEC
        if pd.notna(row.get("Date Added")) and end_dt < row.get("Date Added"):
            end_dt = row.get("Date Added")
        df.at[idx, "Date Started"] = start_dt
        df.at[idx, "Date Finished"] = end_dt

    return df

