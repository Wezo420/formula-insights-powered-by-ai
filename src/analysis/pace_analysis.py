"""
Race Pace Analysis module.
Compares smoothed lap times across drivers, removes outliers,
and computes descriptive pace statistics.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional

from src.processing.clean_data import clean_lap_times, drop_laps_below_threshold
from src.processing.feature_engineering import add_smoothed_lap_time
from utils.logger import get_logger

log = get_logger(__name__)


def compute_pace_summary(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Return per-driver pace statistics.

    Columns: Driver, MedianLapTime, MeanLapTime, BestLapTime,
             StdLapTime, LapCount.
    """
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        return pd.DataFrame()

    clean = clean_lap_times(laps, "LapTimeSeconds")
    clean = drop_laps_below_threshold(clean, "LapTimeSeconds", 60.0)

    if clean.empty:
        return pd.DataFrame()

    summary = (
        clean.groupby("Driver")["LapTimeSeconds"]
        .agg(
            MedianLapTime="median",
            MeanLapTime="mean",
            BestLapTime="min",
            StdLapTime="std",
            LapCount="count",
        )
        .reset_index()
    )
    summary = summary.sort_values("MedianLapTime")
    return summary


def get_smoothed_laps(laps: pd.DataFrame, drivers: list[str]) -> pd.DataFrame:
    """Return cleaned + smoothed lap times for the given drivers."""
    if laps.empty:
        return pd.DataFrame()

    filtered = laps[laps["Driver"].isin(drivers)].copy()
    clean = clean_lap_times(filtered, "LapTimeSeconds")
    clean = drop_laps_below_threshold(clean, "LapTimeSeconds", 60.0)
    enriched = add_smoothed_lap_time(clean, "LapTimeSeconds", window=3)
    return enriched.sort_values(["Driver", "LapNumber"])


def compute_pace_gap(laps: pd.DataFrame, driver_a: str, driver_b: str) -> pd.DataFrame:
    """
    Lap-by-lap pace gap between two drivers.
    Returns DataFrame with LapNumber and PaceGap (A − B in seconds).
    """
    data = get_smoothed_laps(laps, [driver_a, driver_b])
    if data.empty:
        return pd.DataFrame()

    pivot = data.pivot_table(
        index="LapNumber",
        columns="Driver",
        values="LapTimeSeconds",
        aggfunc="median",
    )
    if driver_a not in pivot.columns or driver_b not in pivot.columns:
        return pd.DataFrame()

    gap = pivot[[driver_a, driver_b]].copy()
    gap["PaceGap"] = gap[driver_a] - gap[driver_b]
    gap = gap.reset_index()
    return gap


def identify_fastest_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Return each driver's single fastest (minimum) lap time row."""
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        return pd.DataFrame()

    clean = clean_lap_times(laps, "LapTimeSeconds")
    idx = clean.groupby("Driver")["LapTimeSeconds"].idxmin()
    fastest = clean.loc[idx].reset_index(drop=True)
    return fastest.sort_values("LapTimeSeconds")
