"""
Tyre Strategy Analysis module.
Extracts stints, pit stops, compound sequences, and strategy comparisons.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from src.processing.feature_engineering import add_stint_info, add_tyre_age
from utils.logger import get_logger

log = get_logger(__name__)


def extract_stints(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Build a stint-level DataFrame from lap data.

    Columns: Driver, StintNumber, Compound, StartLap, EndLap, StintLength,
             AvgLapTime, BestLapTime.
    """
    if laps.empty:
        return pd.DataFrame()

    df = add_stint_info(laps)
    df = add_tyre_age(df)

    records = []
    for (driver, stint_no), group in df.groupby(["Driver", "StintNumber"]):
        compound = group["Compound"].mode().iloc[0] if "Compound" in group.columns else "UNKNOWN"
        start_lap = int(group["LapNumber"].min())
        end_lap = int(group["LapNumber"].max())
        length = end_lap - start_lap + 1

        avg_lt = (
            group["LapTimeSeconds"].mean()
            if "LapTimeSeconds" in group.columns
            else None
        )
        best_lt = (
            group["LapTimeSeconds"].min()
            if "LapTimeSeconds" in group.columns
            else None
        )

        records.append(
            {
                "Driver": driver,
                "StintNumber": stint_no,
                "Compound": compound,
                "StartLap": start_lap,
                "EndLap": end_lap,
                "StintLength": length,
                "AvgLapTime": avg_lt,
                "BestLapTime": best_lt,
            }
        )

    return pd.DataFrame(records).sort_values(["Driver", "StintNumber"])


def get_pit_stop_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Return laps on which each driver made a pit stop.
    """
    if laps.empty:
        return pd.DataFrame()

    df = add_stint_info(laps)
    pits = []

    for driver, group in df.groupby("Driver"):
        group = group.sort_values("LapNumber")
        for i in range(1, len(group)):
            prev_row = group.iloc[i - 1]
            curr_row = group.iloc[i]
            if curr_row["StintNumber"] != prev_row["StintNumber"]:
                pits.append(
                    {
                        "Driver": driver,
                        "PitLap": int(prev_row["LapNumber"]),
                        "NewCompound": curr_row.get("Compound", "UNKNOWN"),
                        "OldCompound": prev_row.get("Compound", "UNKNOWN"),
                    }
                )

    return pd.DataFrame(pits)


def compare_strategies(laps: pd.DataFrame, drivers: list[str]) -> pd.DataFrame:
    """Return stint summary filtered to specific drivers."""
    stints = extract_stints(laps)
    if stints.empty:
        return pd.DataFrame()
    return stints[stints["Driver"].isin(drivers)].copy()


def get_compound_distribution(laps: pd.DataFrame) -> pd.DataFrame:
    """Lap count per driver per compound."""
    if laps.empty or "Compound" not in laps.columns:
        return pd.DataFrame()
    dist = (
        laps.groupby(["Driver", "Compound"])
        .size()
        .reset_index(name="LapCount")
    )
    return dist
