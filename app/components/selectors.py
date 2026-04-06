"""
Shared sidebar selector components.
Returns typed user selections for year, GP, session, and drivers.
"""
from __future__ import annotations

import streamlit as st

from config.settings import AVAILABLE_YEARS, DEFAULT_YEAR, DEFAULT_GP, DEFAULT_SESSION
from src.data.fetch_fastf1 import get_gp_names, get_session_drivers
from utils.logger import get_logger

log = get_logger(__name__)

SESSION_OPTIONS = {
    "Race": "R",
    "Qualifying": "Q",
    "Sprint": "S",
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
}


def sidebar_logo() -> None:
    """Render the app logo / branding in the sidebar."""
    st.sidebar.markdown(
        """
        <div style="padding:1rem 0 1.5rem;">
          <div style="
            font-family:'Barlow Condensed',sans-serif;
            font-size:1.5rem;font-weight:800;
            color:#f0f0f5;letter-spacing:0.04em;
            text-transform:uppercase;line-height:1;
          ">
            🏎️ Formula<br>
            <span style="color:#e10600;">Insights AI</span>
          </div>
          <div style="
            font-size:0.65rem;color:#8888a8;
            text-transform:uppercase;letter-spacing:0.12em;
            margin-top:0.3rem;
          ">
            End-to-End F1 Analytics
          </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.07);margin:0 0 1rem;"/>
        """,
        unsafe_allow_html=True,
    )


def selector_year() -> int:
    """Return selected year."""
    return st.sidebar.selectbox(
        "Season",
        options=sorted(AVAILABLE_YEARS, reverse=True),
        index=sorted(AVAILABLE_YEARS, reverse=True).index(DEFAULT_YEAR)
        if DEFAULT_YEAR in AVAILABLE_YEARS
        else 0,
        key="sb_year",
    )


def selector_gp(year: int) -> str:
    """Return selected Grand Prix name."""
    gp_names = get_gp_names(year)
    if not gp_names:
        st.sidebar.warning("No GPs found for this season.")
        return DEFAULT_GP

    default_idx = gp_names.index(DEFAULT_GP) if DEFAULT_GP in gp_names else 0
    return st.sidebar.selectbox(
        "Grand Prix",
        options=gp_names,
        index=default_idx,
        key="sb_gp",
    )


def selector_session() -> str:
    """Return FastF1 session code (e.g. 'R', 'Q')."""
    label = st.sidebar.selectbox(
        "Session",
        options=list(SESSION_OPTIONS.keys()),
        index=0,
        key="sb_session",
    )
    return SESSION_OPTIONS[label]


def selector_drivers(session, max_drivers: int = 20) -> list[str]:
    """
    Multi-select of drivers present in the session.
    Returns list of driver abbreviations.
    """
    drivers = get_session_drivers(session)
    if not drivers:
        st.sidebar.warning("No drivers found in this session.")
        return []

    default = drivers[:2] if len(drivers) >= 2 else drivers
    return st.sidebar.multiselect(
        "Drivers",
        options=drivers,
        default=default,
        max_selections=max_drivers,
        key="sb_drivers",
    )


def selector_two_drivers(session) -> tuple[str, str]:
    """
    Two separate driver selectors for head-to-head comparisons.
    Returns (driver_a, driver_b).
    """
    drivers = get_session_drivers(session)
    if len(drivers) < 2:
        st.sidebar.warning("Need at least 2 drivers.")
        a = drivers[0] if drivers else ""
        return a, a

    a = st.sidebar.selectbox(
        "Driver A",
        options=drivers,
        index=0,
        key="sb_driver_a",
    )
    b_options = [d for d in drivers if d != a]
    b = st.sidebar.selectbox(
        "Driver B",
        options=b_options,
        index=0,
        key="sb_driver_b",
    )
    return a, b


def selector_single_driver(session, label: str = "Driver") -> str:
    """Single driver selector."""
    drivers = get_session_drivers(session)
    if not drivers:
        return ""
    return st.sidebar.selectbox(
        label,
        options=drivers,
        index=0,
        key=f"sb_single_{label}",
    )


def full_session_selectors() -> tuple[int, str, str]:
    """
    Render year + GP + session selectors.
    Returns (year, gp_name, session_code).
    """
    sidebar_logo()
    year = selector_year()
    gp = selector_gp(year)
    session_code = selector_session()
    st.sidebar.markdown("---")
    return year, gp, session_code
