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

    df["Days until finished"] = (df["Date Read"] - df["Date Added"]).dt.days
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

