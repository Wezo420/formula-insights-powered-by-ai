"""
Data cleaning pipeline for lap and telemetry data.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from utils.helpers import remove_outliers_iqr, smooth_series
from utils.logger import get_logger

log = get_logger(__name__)


def clean_lap_times(laps: pd.DataFrame, col: str = "LapTimeSeconds") -> pd.DataFrame:
    """
    Remove in/out laps, safety-car laps, and statistical outliers.
    Returns a copy with cleaned numeric lap-time column.
    """
    if laps.empty or col not in laps.columns:
        return laps

    df = laps.copy()

    # Drop laps without a time
    df = df.dropna(subset=[col])

    # Remove in-lap / out-lap flags
    for flag_col in ["IsOutlap", "IsPersonalBest"]:
        pass  # FastF1 3.x doesn't always have these; skip if absent

    # Remove known slow laps: pit laps, SC laps
    if "PitOutTime" in df.columns:
        df = df[df["PitOutTime"].isna() | (df["LapNumber"] == df["LapNumber"].min())]

    if "TrackStatus" in df.columns:
        # Keep only green-flag laps (TrackStatus == '1')
        df = df[df["TrackStatus"].astype(str).str.startswith("1")]

    # IQR outlier removal per driver
    cleaned_chunks = []
    for driver, group in df.groupby("Driver"):
        group = group.copy()
        group[col] = remove_outliers_iqr(group[col], k=2.0)
        group = group.dropna(subset=[col])
        cleaned_chunks.append(group)

    if not cleaned_chunks:
        return pd.DataFrame(columns=df.columns)

    result = pd.concat(cleaned_chunks, ignore_index=True)
    log.info("clean_lap_times: %d -> %d rows", len(laps), len(result))
    return result


def clean_telemetry(tel: pd.DataFrame) -> pd.DataFrame:
    """
    Remove NaNs and clip unrealistic telemetry values.
    """
    if tel.empty:
        return tel

    df = tel.copy()
    df = df.dropna(subset=["Distance"])

    # Clip throttle and brake to [0, 100]
    for col in ["Throttle", "Brake"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 100)

    # Clip speed to [0, 400] km/h
    if "Speed" in df.columns:
        df["Speed"] = df["Speed"].clip(0, 400)

    # Clip RPM
    if "RPM" in df.columns:
        df["RPM"] = df["RPM"].clip(0, 20000)

    return df.reset_index(drop=True)


def drop_laps_below_threshold(
    laps: pd.DataFrame,
    col: str = "LapTimeSeconds",
    min_seconds: float = 60.0,
) -> pd.DataFrame:
    """Drop laps shorter than *min_seconds* (formation lap artifacts, etc.)."""
    if col not in laps.columns:
        return laps
    return laps[laps[col] >= min_seconds].copy()
