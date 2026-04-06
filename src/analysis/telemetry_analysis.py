"""
Telemetry Analysis module.
Processes speed, throttle, brake, gear, and DRS telemetry data.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from src.processing.clean_data import clean_telemetry
from utils.logger import get_logger

log = get_logger(__name__)


def get_driver_telemetry_comparison(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    driver_a: str,
    driver_b: str,
) -> dict[str, pd.DataFrame]:
    """
    Interpolate and align two drivers' telemetry on a common distance axis.

    Returns dict: {"a": aligned_a, "b": aligned_b, "delta": delta_df}
    """
    if tel_a.empty or tel_b.empty:
        return {}

    a = clean_telemetry(tel_a)
    b = clean_telemetry(tel_b)

    # Common distance grid (every 5 m)
    max_dist = min(a["Distance"].max(), b["Distance"].max())
    dist_grid = np.arange(0, max_dist, 5.0)

    def interp(df: pd.DataFrame, col: str) -> np.ndarray:
        return np.interp(dist_grid, df["Distance"].values, df[col].values)

    cols = ["Speed", "Throttle", "Brake"]
    aligned_a = pd.DataFrame({"Distance": dist_grid})
    aligned_b = pd.DataFrame({"Distance": dist_grid})

    for col in cols:
        if col in a.columns and col in b.columns:
            aligned_a[col] = interp(a, col)
            aligned_b[col] = interp(b, col)

    # Delta: positive = A is faster
    delta = pd.DataFrame({"Distance": dist_grid})
    if "Speed" in aligned_a.columns:
        delta["SpeedDelta"] = aligned_a["Speed"] - aligned_b["Speed"]

    aligned_a["Driver"] = driver_a
    aligned_b["Driver"] = driver_b

    return {"a": aligned_a, "b": aligned_b, "delta": delta}


def compute_braking_zones(tel: pd.DataFrame, threshold_pct: float = 0.1) -> pd.DataFrame:
    """
    Identify braking zones dynamically.
    """
    if tel.empty or "Brake" not in tel.columns:
        return pd.DataFrame()

    df = clean_telemetry(tel)
    
    # Dynamically handle 0-1 boolean scale vs 0-100 percentage scale
    max_brake = df["Brake"].max()
    dynamic_threshold = max_brake * threshold_pct if max_brake > 0 else 5.0
    
    df["Braking"] = df["Brake"] > dynamic_threshold

    zones = []
    in_zone = False
    start = None

    for _, row in df.iterrows():
        if row["Braking"] and not in_zone:
            in_zone = True
            start = row["Distance"]
        elif not row["Braking"] and in_zone:
            in_zone = False
            zone_df = df[
                (df["Distance"] >= start) & (df["Distance"] < row["Distance"])
            ]
            zones.append(
                {
                    "StartDist": start,
                    "EndDist": row["Distance"],
                    "ZoneLength": row["Distance"] - start,
                    "MaxBrake": zone_df["Brake"].max(),
                    "EntrySpeed": zone_df["Speed"].iloc[0] if len(zone_df) > 0 else np.nan,
                }
            )

    return pd.DataFrame(zones)


def compute_sector_mini_sectors(tel: pd.DataFrame, n_sectors: int = 20) -> pd.DataFrame:
    """
    Divide the lap into n_sectors equal-distance mini-sectors.
    Returns avg speed per mini-sector.
    """
    if tel.empty or "Distance" not in tel.columns:
        return pd.DataFrame()

    df = clean_telemetry(tel)
    max_d = df["Distance"].max()
    bins = np.linspace(0, max_d, n_sectors + 1)
    df["MiniSector"] = pd.cut(df["Distance"], bins=bins, labels=False)

    result = df.groupby("MiniSector").agg(
        AvgSpeed=("Speed", "mean"),
        MaxSpeed=("Speed", "max"),
        AvgThrottle=("Throttle", "mean"),
    ).reset_index()
    result["SectorMidDist"] = (bins[:-1] + bins[1:]) / 2
    return result


def summarise_telemetry(tel: pd.DataFrame) -> dict:
    """Return high-level telemetry statistics."""
    if tel.empty:
        return {}

    df = clean_telemetry(tel)
    stats = {}
    if "Speed" in df.columns:
        stats["max_speed"] = round(df["Speed"].max(), 1)
        stats["avg_speed"] = round(df["Speed"].mean(), 1)
        stats["min_speed"] = round(df["Speed"].min(), 1)
    if "Throttle" in df.columns:
        stats["avg_throttle"] = round(df["Throttle"].mean(), 1)
        stats["full_throttle_pct"] = round((df["Throttle"] >= 98).mean() * 100, 1)
    if "Brake" in df.columns:
        # stats["braking_pct"] = round((df["Brake"] > 5).mean() * 100, 1)
        # Dynamically handle 0-1 boolean scale vs 0-100 percentage scale
        max_brake = df["Brake"].max()
        brake_threshold = 5.0 if max_brake > 1.0 else 0.0
        stats["braking_pct"] = round((df["Brake"] > brake_threshold).mean() * 100, 1)
    if "nGear" in df.columns:
        stats["avg_gear"] = round(df["nGear"].mean(), 2)
    return stats
