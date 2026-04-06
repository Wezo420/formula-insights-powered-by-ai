"""
Page 1 — Race Overview
The full race story: results, fastest laps, pace evolution, and top-level stats.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors, selector_drivers
from app.components.charts import lap_time_chart, pace_distribution_chart, cumulative_gap_chart
from src.data.fetch_fastf1 import load_session, get_all_laps, get_race_results, get_session_drivers
from src.analysis.pace_analysis import compute_pace_summary, get_smoothed_laps
from src.processing.feature_engineering import add_smoothed_lap_time
from src.processing.clean_data import clean_lap_times, drop_laps_below_threshold
from utils.helpers import format_lap_time

configure_page("Overview — Formula Insights AI")
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
year, gp, session_code = full_session_selectors()

# ── Load session ──────────────────────────────────────────────────────────────
with st.spinner(f"Loading {year} {gp} session data…"):
    try:
        session = load_session(year, gp, session_code)
        laps_raw = get_all_laps(session)
        results = get_race_results(session)
        drivers = get_session_drivers(session)
    except Exception as e:
        st.error(f"❌ Failed to load session: {e}")
        st.stop()

selected_drivers = selector_drivers(session)
st.sidebar.markdown("---")

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    f"{year} {gp} Grand Prix",
    subtitle=f"{'Race' if session_code == 'R' else session_code} · {len(drivers)} drivers",
    badge="Race Overview",
)

if laps_raw.empty:
    no_data_state("No lap data available for this session.")
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
clean = clean_lap_times(laps_raw, "LapTimeSeconds")
clean = drop_laps_below_threshold(clean, "LapTimeSeconds", 60.0)

total_laps = int(laps_raw["LapNumber"].max()) if not laps_raw.empty else 0
n_drivers = len(drivers)

fastest_driver, fastest_time, fastest_lap_no = "—", "—", "—"
if not clean.empty and "LapTimeSeconds" in clean.columns:
    idx = clean["LapTimeSeconds"].idxmin()
    fastest_driver = clean.loc[idx, "Driver"]
    fastest_time = format_lap_time(clean.loc[idx, "LapTimeSeconds"])
    fastest_lap_no = str(int(clean.loc[idx, "LapNumber"]))

winner = "—"
if not results.empty:
    pos_col = "Position" if "Position" in results.columns else "ClassifiedPosition"
    res_sorted = results.copy()
    res_sorted[pos_col] = pd.to_numeric(res_sorted[pos_col], errors="coerce")
    res_sorted = res_sorted.dropna(subset=[pos_col]).sort_values(pos_col)
    if not res_sorted.empty:
        abbr_col = "Abbreviation" if "Abbreviation" in res_sorted.columns else "FullName"
        winner = str(res_sorted.iloc[0][abbr_col])

kpi_row([
    ("Race Winner", winner, f"{year} {gp}"),
    ("Total Laps", str(total_laps), "Race distance"),
    ("Fastest Lap", fastest_time, f"{fastest_driver} · Lap {fastest_lap_no}"),
    ("Drivers", str(n_drivers), "Classified"),
])

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Race Pace", "🏆 Results", "📊 Distribution", "📉 Gap to Leader"])

# ── Tab 1: Race Pace ─────────────────────────────────────────────────────────
with tab1:
    section_header("Lap Time Evolution")

    plot_drivers = selected_drivers if selected_drivers else drivers[:5]
    smoothed = get_smoothed_laps(laps_raw, plot_drivers)

    if smoothed.empty:
        no_data_state("No cleaned lap data for selected drivers.")
    else:
        fig = lap_time_chart(
            smoothed,
            plot_drivers,
            col="LapTimeSmoothed" if "LapTimeSmoothed" in smoothed.columns else "LapTimeSeconds",
            title="Smoothed Race Pace",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Pace summary table
    section_header("Pace Summary")
    pace_df = compute_pace_summary(laps_raw)
    if not pace_df.empty:
        pace_display = pace_df.copy()
        for col in ["MedianLapTime", "MeanLapTime", "BestLapTime"]:
            if col in pace_display.columns:
                pace_display[col] = pace_display[col].apply(format_lap_time)
        if "StdLapTime" in pace_display.columns:
            pace_display["StdLapTime"] = pace_display["StdLapTime"].apply(
                lambda x: f"{x:.3f}s" if pd.notna(x) else "—"
            )
        st.dataframe(
            pace_display,
            use_container_width=True,
            hide_index=True,
        )

# ── Tab 2: Results ────────────────────────────────────────────────────────────
with tab2:
    section_header("Race Classification")
    if results.empty:
        no_data_state("Results not available for this session.")
    else:
        display_results = results.copy()
        # Clean up position columns
        for col in ["Position", "ClassifiedPosition", "GridPosition"]:
            if col in display_results.columns:
                display_results[col] = pd.to_numeric(display_results[col], errors="coerce")

        pos_col = "Position" if "Position" in display_results.columns else "ClassifiedPosition"
        if pos_col in display_results.columns:
            display_results = display_results.sort_values(pos_col)
        display_results = display_results.dropna(axis=1, how='all')
        st.dataframe(display_results, use_container_width=True, hide_index=True)

# ── Tab 3: Distribution ───────────────────────────────────────────────────────
with tab3:
    section_header("Pace Distribution (Violin)")
    plot_drivers = selected_drivers if selected_drivers else drivers[:8]
    if clean.empty:
        no_data_state()
    else:
        fig = pace_distribution_chart(clean, plot_drivers, title="Lap Time Distribution")
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 4: Gap to Leader ─────────────────────────────────────────────────────
with tab4:
    section_header("Cumulative Gap to Leader")

    if not drivers:
        no_data_state()
    else:
        leader = st.selectbox(
            "Select reference driver (leader)",
            options=drivers,
            index=0,
            key="ov_leader",
        )
        plot_drivers = selected_drivers if selected_drivers else drivers[:5]
        fig = cumulative_gap_chart(clean, plot_drivers, leader, title=f"Gap to {leader}")
        st.plotly_chart(fig, use_container_width=True)
