"""
AI Race Summariser.
Produces structured race reports using Groq + processed session data.
"""
from __future__ import annotations

import pandas as pd

from ai.groq_client import chat_completion
from ai.prompts import race_summary_prompt
from utils.helpers import format_lap_time
from utils.logger import get_logger

log = get_logger(__name__)


def generate_race_summary(
    session,
    laps: pd.DataFrame,
    results: pd.DataFrame,
    stints: pd.DataFrame,
    year: int,
    gp: str,
) -> str:
    """
    Generate a full race report as a markdown string.
    """
    try:
        # Winner
        winner = "Unknown"
        top5: list[str] = []
        if not results.empty:
            sorted_results = results.copy()
            pos_col = "Position" if "Position" in sorted_results.columns else "ClassifiedPosition"
            sorted_results[pos_col] = pd.to_numeric(
                sorted_results[pos_col], errors="coerce"
            )
            sorted_results = sorted_results.dropna(subset=[pos_col]).sort_values(pos_col)
            top_rows = sorted_results.head(5)
            abbr_col = "Abbreviation" if "Abbreviation" in top_rows.columns else "FullName"
            top5 = top_rows[abbr_col].tolist()
            winner = top5[0] if top5 else "Unknown"

        # Key stats
        total_laps = int(laps["LapNumber"].max()) if not laps.empty else 0
        fastest_driver = "Unknown"
        fastest_time = "N/A"
        if not laps.empty and "LapTimeSeconds" in laps.columns:
            idx = laps["LapTimeSeconds"].idxmin()
            fastest_driver = laps.loc[idx, "Driver"]
            fastest_time = format_lap_time(laps.loc[idx, "LapTimeSeconds"])

        key_stats = {
            "total_laps": total_laps,
            "fastest_lap_driver": fastest_driver,
            "fastest_lap_time": fastest_time,
            "safety_cars": "N/A",
            "lead_changes": "N/A",
        }

        # Strategy notes
        strategy_notes = _build_strategy_notes(stints)

        system, user = race_summary_prompt(
            year=year,
            gp=gp,
            winner=winner,
            top5=top5,
            key_stats=key_stats,
            strategy_notes=strategy_notes,
        )
        summary = chat_completion(system, user, max_tokens=1500)
        return summary

    except Exception as exc:
        log.error("Race summary generation failed: %s", exc)
        return "⚠️ Could not generate race summary. Please try again."


def _build_strategy_notes(stints: pd.DataFrame) -> str:
    if stints.empty:
        return "No strategy data available."
    lines = []
    for driver, grp in stints.groupby("Driver"):
        parts = []
        for _, row in grp.iterrows():
            parts.append(
                f"{row['Compound']} ({row['StintLength']} laps)"
            )
        lines.append(f"  {driver}: {' → '.join(parts)}")
    return "\n".join(lines)
