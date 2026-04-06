"""
Feature engineering: derive additional columns from raw FastF1 data.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from utils.helpers import smooth_series
from utils.logger import get_logger

log = get_logger(__name__)


def add_stint_info(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Add StintNumber and LapInStint columns by detecting pit stops.
    """
    if laps.empty:
        return laps

    df = laps.copy()
    df = df.sort_values(["Driver", "LapNumber"]).reset_index(drop=True)

    stint_numbers = []
    lap_in_stint = []

    for driver, group in df.groupby("Driver"):
        stint = 1
        lap_count = 1
        prev_compound = None

        for _, row in group.iterrows():
            compound = row.get("Compound", "UNKNOWN")
            if prev_compound is not None and compound != prev_compound:
                stint += 1
                lap_count = 1
            stint_numbers.append(stint)
            lap_in_stint.append(lap_count)
            prev_compound = compound
            lap_count += 1

    df["StintNumber"] = stint_numbers
    df["LapInStint"] = lap_in_stint
    return df


def add_smoothed_lap_time(
    laps: pd.DataFrame,
    col: str = "LapTimeSeconds",
    window: int = 3,
) -> pd.DataFrame:
    """Add a smoothed lap time column per driver."""
    if laps.empty or col not in laps.columns:
        return laps

    df = laps.copy()
    smoothed = []

    for _, group in df.sort_values(["Driver", "LapNumber"]).groupby("Driver"):
        s = smooth_series(group[col], window=window)
        smoothed.append(s)

    if smoothed:
        df["LapTimeSmoothed"] = pd.concat(smoothed).reindex(df.index)

    return df


def compute_cumulative_time(laps: pd.DataFrame, col: str = "LapTimeSeconds") -> pd.DataFrame:
    """Add CumulativeTime column (running total of lap times per driver)."""
    if laps.empty or col not in laps.columns:
        return laps

    df = laps.copy()
    df = df.sort_values(["Driver", "LapNumber"]).reset_index(drop=True)
    df["CumulativeTime"] = df.groupby("Driver")[col].cumsum()
    return df


def compute_delta_to_leader(laps: pd.DataFrame, leader: str) -> pd.DataFrame:
    """
    Compute lap-by-lap time delta of all drivers vs *leader*.
    Adds DeltaToLeader column (positive = behind leader).
    """
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        return laps

    df = compute_cumulative_time(laps, "LapTimeSeconds")

    leader_df = df[df["Driver"] == leader][["LapNumber", "CumulativeTime"]].copy()
    leader_df = leader_df.rename(columns={"CumulativeTime": "LeaderCumTime"})

    merged = df.merge(leader_df, on="LapNumber", how="left")
    merged["DeltaToLeader"] = merged["CumulativeTime"] - merged["LeaderCumTime"]
    return merged


def add_tyre_age(laps: pd.DataFrame) -> pd.DataFrame:
    """Alias: TyreLife is already in FastF1; ensure column exists."""
    df = laps.copy()
    if "TyreLife" not in df.columns and "LapInStint" in df.columns:
        df["TyreLife"] = df["LapInStint"]
    return df
