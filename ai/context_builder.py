"""
Context builder: converts DataFrames + analysis results into
structured text that AI prompts can consume.
"""
from __future__ import annotations

import pandas as pd

from utils.helpers import format_lap_time
from utils.logger import get_logger

log = get_logger(__name__)


def build_race_context(
    laps: pd.DataFrame,
    results: pd.DataFrame,
    stints: pd.DataFrame,
    year: int,
    gp: str,
) -> str:
    """
    Build a comprehensive race context string for AI prompts.
    """
    lines = [f"=== {year} {gp} Grand Prix ===\n"]

    # ── Race results ──────────────────────────────────────────────────────────
    if not results.empty:
        lines.append("RACE RESULTS:")
        for _, row in results.head(10).iterrows():
            pos = row.get("Position", row.get("ClassifiedPosition", "?"))
            drv = row.get("Abbreviation", row.get("FullName", "?"))
            team = row.get("TeamName", "?")
            lines.append(f"  P{pos} — {drv} ({team})")
        lines.append("")

    # ── Lap time summary ──────────────────────────────────────────────────────
    if not laps.empty and "LapTimeSeconds" in laps.columns:
        lines.append("LAP TIME SUMMARY (per driver):")
        summary = (
            laps.groupby("Driver")["LapTimeSeconds"]
            .agg(["min", "mean", "count"])
            .reset_index()
        )
        for _, row in summary.sort_values("mean").iterrows():
            lines.append(
                f"  {row['Driver']}: Best={format_lap_time(row['min'])}, "
                f"Avg={format_lap_time(row['mean'])}, Laps={int(row['count'])}"
            )
        lines.append("")

    # ── Strategy overview ─────────────────────────────────────────────────────
    if not stints.empty:
        lines.append("STINT / STRATEGY OVERVIEW:")
        for driver, grp in stints.groupby("Driver"):
            strat = " → ".join(
                f"{row['Compound']}({row['StintLength']}L)"
                for _, row in grp.iterrows()
            )
            lines.append(f"  {driver}: {strat}")
        lines.append("")

    return "\n".join(lines)


def build_telemetry_context(
    telemetry_stats: dict,
    driver: str,
    lap_times: list[float],
) -> str:
    lines = [
        f"=== Telemetry Summary — {driver} ===",
        f"Max Speed      : {telemetry_stats.get('max_speed', 'N/A')} km/h",
        f"Avg Speed      : {telemetry_stats.get('avg_speed', 'N/A')} km/h",
        f"Full Throttle  : {telemetry_stats.get('full_throttle_pct', 'N/A')}% of lap",
        f"Braking        : {telemetry_stats.get('braking_pct', 'N/A')}% of lap",
        f"Avg Gear       : {telemetry_stats.get('avg_gear', 'N/A')}",
        "",
        f"Recent Lap Times (s): {[round(lt, 3) for lt in lap_times[-10:]]}",
    ]
    return "\n".join(lines)


def build_driver_battle_context(
    driver_a: str,
    driver_b: str,
    pace_summary: pd.DataFrame,
    stints: pd.DataFrame,
) -> tuple[float, dict, str]:
    """
    Returns (pace_gap, sector_deltas, strategy_diff_text).
    """
    pace_gap = 0.0
    if not pace_summary.empty and "MedianLapTime" in pace_summary.columns:
        row_a = pace_summary[pace_summary["Driver"] == driver_a]
        row_b = pace_summary[pace_summary["Driver"] == driver_b]
        if not row_a.empty and not row_b.empty:
            pace_gap = row_a.iloc[0]["MedianLapTime"] - row_b.iloc[0]["MedianLapTime"]

    sector_deltas: dict[str, str] = {}
    for sector, col in [("s1", "Sector1TimeSeconds"), ("s2", "Sector2TimeSeconds"), ("s3", "Sector3TimeSeconds")]:
        sector_deltas[sector] = "N/A"

    strategy_diff = "N/A"
    if not stints.empty:
        def fmt_strat(drv: str) -> str:
            drv_stints = stints[stints["Driver"] == drv]
            if drv_stints.empty:
                return "Unknown"
            return " → ".join(
                f"{r['Compound']}({r['StintLength']}L)"
                for _, r in drv_stints.iterrows()
            )

        strategy_diff = (
            f"{driver_a}: {fmt_strat(driver_a)}\n"
            f"{driver_b}: {fmt_strat(driver_b)}"
        )

    return pace_gap, sector_deltas, strategy_diff


def build_strategy_context(stints: pd.DataFrame, deg_df: pd.DataFrame) -> tuple[str, str]:
    """
    Returns (strategy_summary_text, degradation_summary_text).
    """
    strat_lines = []
    for driver, grp in stints.groupby("Driver"):
        parts = []
        for _, row in grp.iterrows():
            avg_lt = format_lap_time(row.get("AvgLapTime"))
            parts.append(
                f"{row['Compound']} {row['StintLength']} laps "
                f"(L{row['StartLap']}–L{row['EndLap']}, avg {avg_lt})"
            )
        strat_lines.append(f"{driver}: {' → '.join(parts)}")
    strategy_summary = "\n".join(strat_lines) if strat_lines else "No strategy data available."

    deg_lines = []
    if not deg_df.empty:
        for _, row in deg_df.iterrows():
            sign = "+" if row["DegradationRate"] > 0 else ""
            deg_lines.append(
                f"{row['Driver']} Stint {int(row['StintNumber'])} "
                f"({row['Compound']}): {sign}{row['DegradationRate']:.4f} s/lap"
            )
    degradation_summary = "\n".join(deg_lines) if deg_lines else "No degradation data."

    return strategy_summary, degradation_summary
