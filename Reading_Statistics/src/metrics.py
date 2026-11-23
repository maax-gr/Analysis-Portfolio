"""Metrics and aggregation functions for the Reading Dashboard.

Implements two functions used by the dashboard:
- `books_per_month`: counts books read per month (by `Date Read`).
- `pages_over_time`: constructs a timeseries of pages read per day using
  the `average pages read per day` allocation algorithm from the spec.
"""
from typing import Tuple
import pandas as pd


def books_per_month(df: pd.DataFrame) -> pd.Series:
    """Aggregate number of books read per month.

    Returns a Series indexed by month timestamps with integer counts.
    Only rows where `Exclusive Shelf` is 'read' and `Date Read` exists are
    counted.

    Implementation notes for readability:
    - We build a boolean mask to select only relevant rows.
    - `pd.Grouper(..., freq='MS')` groups rows by calendar month based on
      the `Date Read` column.
    - The result of `groupby.size()` has a DatetimeIndex at month-start; we
      convert it to a month-aligned timestamp for easier plotting.
    """
    # Select rows that should be counted: shelf must be 'read' and we need a date
    mask = (
        df["Exclusive Shelf"].notna()
        & (df["Exclusive Shelf"] == "read")
        & df["Date Read"].notna()
    )

    # Work on a copy of the filtered DataFrame
    df2 = df.loc[mask].copy()

    # If nothing matches, return an empty Series of ints
    if df2.empty:
        return pd.Series(dtype="int")

    # Group by month (calendar month) and count entries per month
    s = df2.groupby(pd.Grouper(key="Date Read", freq="MS")).size()

    # Convert the index to a month-aligned timestamp (useful for plotting)
    s.index = s.index.to_period("M").to_timestamp()
    return s


def pages_over_time(df: pd.DataFrame, start: pd.Timestamp = None, end: pd.Timestamp = None) -> pd.Series:
    """Return daily timeseries of pages read per day.

    Algorithm: for each book with a non-null `average pages read per day`,
    add that daily value to every date between `Date Started` and
    `Date Finished` inclusive.

    Parameters
    - df: enriched DataFrame containing `Date Started`, `Date Finished`, and
      `average pages read per day`.
    - start, end: optional range to limit the output. Defaults to min(Date Started) .. today.
    """
    # Work on a copy to avoid mutating caller data
    df = df.copy()

    # Keep only rows that have the necessary fields
    mask = (
        df["average pages read per day"].notna()
        & df["Date Started"].notna()
        & df["Date Finished"].notna()
    )
    # We only need the three columns for the allocation algorithm
    df_valid = df.loc[mask, ["Date Started", "Date Finished", "average pages read per day"]]

    # If there's no valid data, return an empty float Series
    if df_valid.empty:
        return pd.Series(dtype="float")

    # Determine the output range. Default: from earliest Date Started to today.
    if start is None:
        start = df_valid["Date Started"].min()
    if end is None:
        end = pd.Timestamp.now().normalize()

    if pd.isna(start) or pd.isna(end) or start > end:
        return pd.Series(dtype="float")

    # Create an index for every day in the requested range
    all_days = pd.date_range(start=start.normalize(), end=end.normalize(), freq="D")
    # Initialize a series of zeros (float) which we'll add daily allocations into
    series = pd.Series(0.0, index=all_days)

    # For each book, add its per-day contribution to every day between
    # Date Started and Date Finished (inclusive). This is simple and easy to
    # understand, and works well for modest-sized personal datasets.
    for _, row in df_valid.iterrows():
        # normalize timestamps to midnight so slicing matches the index
        s = row["Date Started"].normalize()
        e = row["Date Finished"].normalize()
        daily = float(row["average pages read per day"])

        # Clip the book's interval to the series range so we don't attempt
        # to write outside the bounds of `series`
        s2 = max(s, series.index[0])
        e2 = min(e, series.index[-1])

        # If the clipped interval is empty, skip this book
        if s2 > e2:
            continue

        # Add the daily page count to every day in the interval. Pandas
        # allows label-based slicing like series.loc[s2:e2] which is handy
        # here and keeps the code readable.
        series.loc[s2:e2] += daily

    # The result is a daily time series (float) representing pages read per day
    return series
