"""
Primary FastF1 data fetching layer.
All functions return clean DataFrames or raise descriptive exceptions.
"""
from __future__ import annotations

import pandas as pd
import fastf1
import streamlit as st

from src.data.cache_manager import init_cache
from utils.logger import get_logger
from utils.helpers import timedelta_to_seconds

log = get_logger(__name__)


def _ensure_cache() -> None:
    init_cache()


# ── Session loader ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_session(year: int, gp: str, session_type: str) -> fastf1.core.Session:
    """
    Load and return a FastF1 session object.
    Results are cached for 1 hour via st.cache_data.
    """
    _ensure_cache()
    log.info("Loading session: %d %s %s", year, gp, session_type)
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load(
            laps=True,
            telemetry=True,
            weather=False,
            messages=False,
        )
        log.info("Session loaded successfully: %d %s %s", year, gp, session_type)
        return session
    except Exception as exc:
        log.error("Failed to load session %d %s %s: %s", year, gp, session_type, exc)
        raise RuntimeError(
            f"Could not load session {year} {gp} {session_type}.\n"
            f"Reason: {exc}"
        ) from exc


# ── Grand Prix list ────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def get_event_schedule(year: int) -> pd.DataFrame:
    """Return the full event schedule for *year* as a DataFrame."""
    _ensure_cache()
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        return schedule[["EventName", "EventDate", "Country", "Location"]].copy()
    except Exception as exc:
        log.error("Failed to get schedule for %d: %s", year, exc)
        return pd.DataFrame(columns=["EventName", "EventDate", "Country", "Location"])


@st.cache_data(ttl=86400, show_spinner=False)
def get_gp_names(year: int) -> list[str]:
    """Return sorted list of Grand Prix names for *year*."""
    schedule = get_event_schedule(year)
    if schedule.empty:
        return ["Bahrain", "Saudi Arabia", "Australia"]
    return schedule["EventName"].tolist()


# ── Lap data ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_all_laps(_session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract all laps from a session with pre-processed time columns.
    Returns a DataFrame with consistent, numeric time columns.
    """
    try:
        laps = _session.laps.copy()
        # Convert Timedelta columns to float seconds
        for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
            if col in laps.columns:
                laps[f"{col}Seconds"] = laps[col].apply(timedelta_to_seconds)
        # Ensure numeric lap number
        laps["LapNumber"] = pd.to_numeric(laps["LapNumber"], errors="coerce")
        log.info("Extracted %d laps from session", len(laps))
        return laps
    except Exception as exc:
        log.error("Failed to extract laps: %s", exc)
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_driver_laps(
    _session: fastf1.core.Session, driver: str
) -> pd.DataFrame:
    """Return laps for a single driver, enriched with numeric time cols."""
    all_laps = get_all_laps(_session)
    if all_laps.empty:
        return pd.DataFrame()
    mask = all_laps["Driver"] == driver
    return all_laps[mask].copy().reset_index(drop=True)


# ── Driver list ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_session_drivers(_session: fastf1.core.Session) -> list[str]:
    """Return sorted list of driver abbreviations (NOT numbers)."""
    try:
        # Extract abbreviations directly from lap data to ensure 100% Pandas match
        if _session.laps is not None and not _session.laps.empty:
            drivers = _session.laps["Driver"].dropna().unique().tolist()
            log.info("Session drivers: %s", drivers)
            return sorted(drivers)
        return sorted(_session.drivers)
    except Exception as exc:
        log.error("Failed to get session drivers: %s", exc)
        return []


# ── Telemetry ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_fastest_lap_telemetry(
    _session: fastf1.core.Session, driver: str
) -> pd.DataFrame:
    """Return telemetry for a driver's fastest lap, distance-indexed."""
    try:
        laps = _session.laps.pick_driver(driver)
        fastest = laps.pick_fastest()
        if fastest is None or fastest.empty:
            log.warning("No fastest lap found for %s", driver)
            return pd.DataFrame()
        tel = fastest.get_car_data().add_distance()
        log.info("Telemetry loaded for %s (%d rows)", driver, len(tel))
        return tel
    except Exception as exc:
        log.error("Failed to get telemetry for %s: %s", driver, exc)
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_lap_telemetry(
    _session: fastf1.core.Session, driver: str, lap_number: int
) -> pd.DataFrame:
    """Return telemetry for a specific lap number and driver."""
    try:
        laps = _session.laps.pick_driver(driver)
        lap = laps[laps["LapNumber"] == lap_number]
        if lap.empty:
            return pd.DataFrame()
        tel = lap.iloc[0].get_car_data().add_distance()
        return tel
    except Exception as exc:
        log.error("Failed to get lap %d telemetry for %s: %s", lap_number, driver, exc)
        return pd.DataFrame()


# ── Results ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_race_results(_session: fastf1.core.Session) -> pd.DataFrame:
    """Return final race result DataFrame with Ergast fallback."""
    try:
        results = _session.results
        if results is None or results.empty:
            return pd.DataFrame()

        res = results.copy()

        # 1. ERGAST FALLBACK: If Position is entirely missing or NaN, build it
        if "Position" not in res.columns or res["Position"].isna().all():
            log.warning("Ergast Position data missing. Deriving fallback positions.")
            
            # Try parsing from ClassifiedPosition first (F1 livetiming data)
            if "ClassifiedPosition" in res.columns:
                numeric_pos = pd.to_numeric(res["ClassifiedPosition"], errors="coerce")
                if not numeric_pos.isna().all():
                    res["Position"] = numeric_pos

            # If still completely empty, derive mathematically from lap data
            if "Position" not in res.columns or res["Position"].isna().all():
                laps = _session.laps
                if laps is not None and not laps.empty:
                    last_laps = laps.loc[laps.groupby("Driver")["LapNumber"].idxmax()]
                    # Sort by max laps descending, then by total time ascending
                    last_laps = last_laps.sort_values(["LapNumber", "Time"], ascending=[False, True])
                    last_laps["CalculatedPos"] = range(1, len(last_laps) + 1)
                    pos_map = last_laps.set_index("Driver")["CalculatedPos"].to_dict()
                    res["Position"] = res["Abbreviation"].map(pos_map)
                else:
                    res["Position"] = range(1, len(res) + 1)

        # 2. Ensure all UI required columns exist so Pandas doesn't crash
        expected_cols = [
            "DriverNumber", "Abbreviation", "FullName", "TeamName",
            "GridPosition", "Position", "ClassifiedPosition",
            "Points", "Status", "Time"
        ]
        
        for col in expected_cols:
            if col not in res.columns:
                res[col] = None

        return res[expected_cols]
    except Exception as exc:
        log.error("Failed to get race results: %s", exc)
        return pd.DataFrame()

# @st.cache_data(ttl=3600, show_spinner=False)
# def get_race_results(_session: fastf1.core.Session) -> pd.DataFrame:
#     """Return final race result DataFrame."""
#     try:
#         results = _session.results
#         if results is None:
#             return pd.DataFrame()
#         cols = [
#             c for c in [
#                 "DriverNumber", "Abbreviation", "FullName", "TeamName",
#                 "GridPosition", "Position", "ClassifiedPosition",
#                 "Points", "Status", "Time",
#             ]
#             if c in results.columns
#         ]
#         return results[cols].copy()
#     except Exception as exc:
#         log.error("Failed to get race results: %s", exc)
#         return pd.DataFrame()
