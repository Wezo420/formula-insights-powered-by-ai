"""
Page 6 — Race Summary
AI-generated full race report with key moments, strategy, and verdict.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors
from app.components.charts import strategy_chart, lap_time_chart
from src.data.fetch_fastf1 import load_session, get_all_laps, get_race_results
from src.analysis.strategy_analysis import extract_stints
from src.analysis.pace_analysis import identify_fastest_laps, get_smoothed_laps
from src.processing.clean_data import clean_lap_times
from ai.summarizer import generate_race_summary
from utils.helpers import format_lap_time

configure_page("Race Summary — Formula Insights AI")
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
year, gp, session_code = full_session_selectors()

with st.spinner("Loading session…"):
    try:
        session = load_session(year, gp, session_code)
        laps_raw = get_all_laps(session)
        results = get_race_results(session)
    except Exception as e:
        st.error(f"❌ {e}")
        st.stop()

page_header(
    "Race Report",
    subtitle=f"{year} {gp} Grand Prix",
    badge="Race Summary",
)

# ── Quick stats ───────────────────────────────────────────────────────────────
clean_laps = clean_lap_times(laps_raw, "LapTimeSeconds")

fastest_driver, fastest_time = "—", "—"
if not clean_laps.empty and "LapTimeSeconds" in clean_laps.columns:
    idx = clean_laps["LapTimeSeconds"].idxmin()
    fastest_driver = clean_laps.loc[idx, "Driver"]
    fastest_time = format_lap_time(clean_laps.loc[idx, "LapTimeSeconds"])

winner = "—"
pos_col = "Position" if "Position" in results.columns else "ClassifiedPosition"
if not results.empty and pos_col in results.columns:
    sorted_r = results.copy()
    sorted_r[pos_col] = pd.to_numeric(sorted_r[pos_col], errors="coerce")
    sorted_r = sorted_r.dropna(subset=[pos_col]).sort_values(pos_col)
    if not sorted_r.empty:
        abbr = "Abbreviation" if "Abbreviation" in sorted_r.columns else "FullName"
        winner = str(sorted_r.iloc[0][abbr])

total_laps = int(laps_raw["LapNumber"].max()) if not laps_raw.empty else 0
n_drivers = int(laps_raw["Driver"].nunique()) if not laps_raw.empty else 0

kpi_row([
    ("Race Winner", winner, f"{year} {gp}"),
    ("Total Laps", str(total_laps), "Race distance"),
    ("Fastest Lap", fastest_time, fastest_driver),
    ("Starters", str(n_drivers), "Drivers"),
])
st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📰 AI Race Report", "🏆 Classification", "📈 Race Pace"])

# ── Tab 1: AI Report ─────────────────────────────────────────────────────────
with tab1:
    section_header("AI-Generated Race Report")

    # Cache report in session state
    cache_key = f"race_report_{year}_{gp}_{session_code}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = None

    col1, col2 = st.columns([1, 5])
    with col1:
        generate = st.button("🤖 Generate Report", key="gen_report", use_container_width=True)
    with col2:
        if st.session_state[cache_key]:
            if st.button("🔄 Regenerate", key="regen_report"):
                st.session_state[cache_key] = None
                st.rerun()

    if generate:
        stints = extract_stints(laps_raw)
        with st.spinner("Writing race report… (this may take 10–15 seconds)"):
            report = generate_race_summary(session, laps_raw, results, stints, year, gp)
        st.session_state[cache_key] = report

    if st.session_state[cache_key]:
        with st.container(border=True):
            st.markdown(st.session_state[cache_key])
    elif not generate:
        st.markdown(
            """
            <div style="
                text-align:center;padding:4rem 2rem;
                border:1px dashed rgba(255,255,255,0.1);border-radius:6px;
            ">
                <div style="font-size:3rem;margin-bottom:1rem;">📰</div>
                <div style="
                    font-family:'Barlow Condensed',sans-serif;
                    font-size:1.1rem;font-weight:700;
                    color:#8888a8;text-transform:uppercase;letter-spacing:0.08em;
                ">Click "Generate Report" to create an AI race report</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Tab 2: Classification ─────────────────────────────────────────────────────
with tab2:
    section_header("Race Classification")
    if results.empty:
        no_data_state("Classification not available.")
    else:
        display = results.copy()
        for c in [pos_col, "GridPosition"]:
            if c in display.columns:
                display[c] = pd.to_numeric(display[c], errors="coerce")
        if pos_col in display.columns:
            display = display.sort_values(pos_col)

        fastest_laps = identify_fastest_laps(laps_raw)
        if not fastest_laps.empty:
            fl_map = fastest_laps.set_index("Driver")["LapTimeSeconds"].to_dict()
            abbr_col = "Abbreviation" if "Abbreviation" in display.columns else "FullName"
            if abbr_col in display.columns:
                display["FastestLap"] = display[abbr_col].map(
                    lambda d: format_lap_time(fl_map.get(d))
                )
        display = display.dropna(axis=1, how='all')
        st.dataframe(display, use_container_width=True, hide_index=True)

# ── Tab 3: Race Pace ─────────────────────────────────────────────────────────
with tab3:
    section_header("Race Pace — Top 10")

    top10_drivers = []
    if not results.empty and pos_col in results.columns:
        r = results.copy()
        r[pos_col] = pd.to_numeric(r[pos_col], errors="coerce")
        r = r.dropna(subset=[pos_col]).sort_values(pos_col).head(10)
        abbr_col = "Abbreviation" if "Abbreviation" in r.columns else "FullName"
        top10_drivers = r[abbr_col].tolist()

    if not top10_drivers:
        top10_drivers = laps_raw["Driver"].unique().tolist()[:10]

    smoothed = get_smoothed_laps(laps_raw, top10_drivers)
    if smoothed.empty:
        no_data_state()
    else:
        col = "LapTimeSmoothed" if "LapTimeSmoothed" in smoothed.columns else "LapTimeSeconds"
        fig = lap_time_chart(smoothed, top10_drivers, col=col, title="Race Pace — Top 10")
        st.plotly_chart(fig, use_container_width=True)

    section_header("Tyre Strategy Overview")
    stints = extract_stints(laps_raw)
    top10_stints = stints[stints["Driver"].isin(top10_drivers)] if not stints.empty else stints
    if not top10_stints.empty:
        fig = strategy_chart(top10_stints, title="Strategy — Top 10")
        st.plotly_chart(fig, use_container_width=True)
