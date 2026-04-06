"""
Tyre Degradation Analysis module.
Models performance drop over a stint using linear regression per compound.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from src.processing.feature_engineering import add_stint_info, add_tyre_age
from src.processing.clean_data import clean_lap_times
from utils.logger import get_logger

log = get_logger(__name__)


def compute_degradation_per_stint(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Fit a linear model to lap times per stint.
    Returns: Driver, StintNumber, Compound, DegradationRate (s/lap), R2.
    """
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        return pd.DataFrame()

    df = add_stint_info(laps)
    df = add_tyre_age(df)
    df = clean_lap_times(df, "LapTimeSeconds")

    records = []
    for (driver, stint_no), group in df.groupby(["Driver", "StintNumber"]):
        group = group.dropna(subset=["LapTimeSeconds", "LapInStint"])
        if len(group) < 3:
            continue

        x = group["LapInStint"].values.astype(float)
        y = group["LapTimeSeconds"].values.astype(float)

        try:
            coeffs = np.polyfit(x, y, 1)
            degradation_rate = round(coeffs[0], 4)  # s/lap

            # R²
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2 = round(1 - ss_res / ss_tot, 3) if ss_tot != 0 else 0.0

            compound = (
                group["Compound"].mode().iloc[0]
                if "Compound" in group.columns
                else "UNKNOWN"
            )
            records.append(
                {
                    "Driver": driver,
                    "StintNumber": stint_no,
                    "Compound": compound,
                    "DegradationRate": degradation_rate,
                    "R2": r2,
                    "StintLength": len(group),
                    "BaseLapTime": round(float(np.polyval(coeffs, 1)), 3),
                }
            )
        except Exception as exc:
            log.warning("Degradation fit failed for %s stint %d: %s", driver, stint_no, exc)

    return pd.DataFrame(records).sort_values(["Driver", "StintNumber"])


def get_compound_degradation_stats(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate degradation rates by compound across all drivers.
    """
    deg = compute_degradation_per_stint(laps)
    if deg.empty:
        return pd.DataFrame()

    stats = (
        deg.groupby("Compound")["DegradationRate"]
        .agg(
            AvgDegRate="mean",
            MaxDegRate="max",
            MinDegRate="min",
            StintCount="count",
        )
        .reset_index()
    )
    return stats


def project_degradation_curve(
    driver: str,
    laps: pd.DataFrame,
    stint_number: int,
    project_laps: int = 10,
) -> pd.DataFrame:
    """
    Project lap times forward using fitted degradation slope.
    Returns DataFrame with LapInStint and ProjectedLapTime.
    """
    df = add_stint_info(laps)
    df = add_tyre_age(df)

    group = df[(df["Driver"] == driver) & (df["StintNumber"] == stint_number)]
    group = group.dropna(subset=["LapTimeSeconds", "LapInStint"])

    if len(group) < 3:
        return pd.DataFrame()

    x = group["LapInStint"].values.astype(float)
    y = group["LapTimeSeconds"].values.astype(float)

    try:
        coeffs = np.polyfit(x, y, 1)
        future_laps = np.arange(x.max() + 1, x.max() + 1 + project_laps)
        projected = np.polyval(coeffs, future_laps)

        actual = pd.DataFrame(
            {"LapInStint": x, "LapTime": y, "Type": "Actual"}
        )
        projected_df = pd.DataFrame(
            {"LapInStint": future_laps, "LapTime": projected, "Type": "Projected"}
        )
        return pd.concat([actual, projected_df], ignore_index=True)
    except Exception as exc:
        log.warning("Projection failed for %s: %s", driver, exc)
        return pd.DataFrame()
