"""Data cleaning utilities for the Reading Dashboard.

Implements loading and cleaning logic described in
`SPEC_Reading_Dashboard.md`. Exposes `load_raw_csv` and
`clean_dataframe` which return pandas DataFrames. The cleaning
step enforces the rules around dates, numeric pages, ratings,
and basic string sanitization.
"""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


RAW_COLUMNS = [
    "Title",
    "Author",
    "Author l-f",
    "ISBN",
    "ISBN13",
    "My Rating",
    "Publisher",
    "Number of Pages",
    "Year Published",
    "Original Publication Year",
    "Date Read",
    "Date Added",
    "Exclusive Shelf",
    "My Review",
]


def load_raw_csv(path: str) -> pd.DataFrame:
    """Load the raw Goodreads CSV as strings (no type coercion).

    Parameters
    - path: path to the raw CSV

    Returns
    - DataFrame with at least the columns in RAW_COLUMNS (missing columns
      are created as NaN).
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    # Ensure all expected columns exist
    for c in RAW_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    # Keep only known columns (preserve others if needed later?)
    return df[RAW_COLUMNS].copy()


def _strip_wrappers(s: pd.Series) -> pd.Series:
    """Strip common quote/wrapper patterns from strings.

    Handles values like `"..."`, `="..."`, etc.
    """
    if s.dtype == object or pd.api.types.is_string_dtype(s):
        return s.astype(str).str.strip().str.replace(r'^=+"|"+$', '', regex=True)
    return s


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """Apply cleaning rules and return cleaned DataFrame plus a report.

    Cleaning rules implemented (per spec):
    - Strip `"` wrappers for `Title`, `Author l-f`, `My Review`, ISBN fields
    - Treat empty strings as null / NaN
    - `My Rating`: convert to integer; 0 => NaN
    - `Number of Pages`: convert to integer or NaN; any non-integer values are
      reported in the returned report
    - Parse `Date Added` and `Date Read` with format YYYY/MM/DD (coerce errors)
    - If `Date Read` is missing but `Date Added` exists, copy `Date Added`
    - If both dates missing => left as NaT
    - If `Date Read` < `Date Added`, set `Date Read` == `Date Added`

    Returns a tuple `(cleaned_df, report)` where `report` contains lists of
    problematic fields (currently `invalid_pages_rows`).
    """
    report: Dict[str, List[str]] = {"invalid_pages_rows": []}

    df = df.copy()

    # Normalize empty strings to NaN
    df.replace({"": pd.NA, "NA": pd.NA, "nan": pd.NA}, inplace=True)

    # Strip wrappers
    df["Title"] = _strip_wrappers(df["Title"]).where(df["Title"].notna(), pd.NA)
    df["Author l-f"] = _strip_wrappers(df["Author l-f"]).where(df["Author l-f"].notna(), pd.NA)
    df["My Review"] = _strip_wrappers(df["My Review"]).where(df["My Review"].notna(), pd.NA)
    df["ISBN"] = _strip_wrappers(df["ISBN"]).where(df["ISBN"].notna(), pd.NA)
    df["ISBN13"] = _strip_wrappers(df["ISBN13"]).where(df["ISBN13"].notna(), pd.NA)

    # Ratings: coerce to numeric ints; 0 -> NaN
    df["My Rating"] = pd.to_numeric(df["My Rating"], errors="coerce").astype("Int64")
    df.loc[df["My Rating"] == 0, "My Rating"] = pd.NA

    # Number of Pages: must be int or null
    def _to_int_pages(x):
        try:
            if pd.isna(x):
                return pd.NA
            # strip whitespace
            xs = str(x).strip()
            if xs == "":
                return pd.NA
            # reject floats like '123.0' as valid integers only if they represent int
            if xs.isdigit():
                return int(xs)
            # allow numbers with commas
            xs2 = xs.replace(",", "")
            if xs2.isdigit():
                return int(xs2)
            # otherwise invalid
            raise ValueError(f"invalid pages: {x}")
        except Exception:
            return None

    pages_converted = df["Number of Pages"].apply(_to_int_pages)
    invalid_mask = pages_converted.isnull() & df["Number of Pages"].notna()
    if invalid_mask.any():
        report["invalid_pages_rows"] = df.loc[invalid_mask, "Title"].astype(str).tolist()
    # Use pandas nullable integer dtype where possible
    df["Number of Pages"] = pages_converted.replace({None: pd.NA}).astype("Int64")

    # Year fields
    df["Year Published"] = pd.to_numeric(df["Year Published"], errors="coerce").astype("Int64")
    df["Original Publication Year"] = pd.to_numeric(df["Original Publication Year"], errors="coerce").astype("Int64")

    # Parse dates (spec expects yyyy/mm/dd but we tolerate coercion)
    df["Date Added"] = pd.to_datetime(df["Date Added"], errors="coerce", infer_datetime_format=True)
    df["Date Read"] = pd.to_datetime(df["Date Read"], errors="coerce", infer_datetime_format=True)

    # If Date Read missing but Date Added exists -> copy
    missing_read = df["Date Read"].isna() & df["Date Added"].notna()
    df.loc[missing_read, "Date Read"] = df.loc[missing_read, "Date Added"]

    # If both missing -> leave as NaT (will be ignored by algorithms)

    # If Date Read < Date Added -> set Date Read == Date Added
    mask_bad_order = df["Date Read"].notna() & df["Date Added"].notna() & (df["Date Read"] < df["Date Added"])
    if mask_bad_order.any():
        df.loc[mask_bad_order, "Date Read"] = df.loc[mask_bad_order, "Date Added"]

    # Standardize Exclusive Shelf capitalization
    df["Exclusive Shelf"] = df["Exclusive Shelf"].astype(str).str.strip().str.lower().replace({"nan": pd.NA})

    return df, report
