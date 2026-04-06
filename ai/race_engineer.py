"""
AI Race Engineer module.
Provides interactive, telemetry-aware coaching and debrief capabilities.
"""
from __future__ import annotations

import pandas as pd

from ai.groq_client import chat_completion, stream_completion
from ai.prompts import race_engineer_feedback, race_engineer_chat
from ai.context_builder import build_race_context, build_telemetry_context
from src.analysis.telemetry_analysis import summarise_telemetry
from utils.logger import get_logger

log = get_logger(__name__)


def get_driver_debrief(
    driver: str,
    year: int,
    gp: str,
    laps: pd.DataFrame,
    telemetry: pd.DataFrame,
    compound: str = "UNKNOWN",
    question: str = "Give me a full performance debrief.",
) -> str:
    """
    Generate a race engineer debrief for a specific driver.
    """
    try:
        tel_stats = summarise_telemetry(telemetry) if not telemetry.empty else {}
        driver_laps = laps[laps["Driver"] == driver] if not laps.empty else pd.DataFrame()
        lap_times = []
        if not driver_laps.empty and "LapTimeSeconds" in driver_laps.columns:
            lap_times = driver_laps["LapTimeSeconds"].dropna().tolist()

        system, user = race_engineer_feedback(
            driver=driver,
            gp=gp,
            year=year,
            telemetry_stats=tel_stats,
            lap_times=lap_times,
            compound=compound,
            question=question,
        )
        return chat_completion(system, user, max_tokens=1200)

    except Exception as exc:
        log.error("Driver debrief failed for %s: %s", driver, exc)
        return "⚠️ Could not generate driver debrief."


def race_engineer_stream_response(
    driver: str,
    year: int,
    gp: str,
    laps: pd.DataFrame,
    results: pd.DataFrame,
    stints: pd.DataFrame,
    telemetry: pd.DataFrame,
    conversation_history: list[dict],
    user_message: str,
):
    """
    Generator: stream race engineer response tokens.
    """
    try:
        # Build context
        context = build_race_context(laps, results, stints, year, gp)
        tel_stats = summarise_telemetry(telemetry) if not telemetry.empty else {}
        tel_context = build_telemetry_context(tel_stats, driver, [])
        full_context = context + "\n" + tel_context

        system, user = race_engineer_chat(
            driver=driver,
            gp=gp,
            year=year,
            context=full_context,
            conversation_history=conversation_history,
            user_message=user_message,
        )
        yield from stream_completion(system, user, max_tokens=800)

    except Exception as exc:
        log.error("Race engineer streaming failed: %s", exc)
        yield "⚠️ Error generating response. Please try again."


def suggest_questions(driver: str, gp: str) -> list[str]:
    """Return pre-built question suggestions for the race engineer chat."""
    return [
        f"Where is {driver} losing the most time per lap?",
        f"How is {driver}'s tyre management compared to the field?",
        f"What braking improvements could {driver} make?",
        f"How did the strategy affect {driver}'s race result?",
        f"Analyse {driver}'s throttle application through the high-speed corners.",
        f"What was {driver}'s biggest strength in the {gp} GP?",
        "Compare my pace to the race leader lap by lap.",
    ]
