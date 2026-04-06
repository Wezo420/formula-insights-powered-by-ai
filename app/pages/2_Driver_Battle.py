"""
Page 2 — Driver Battle
Corner-by-corner head-to-head: delta time, sector gaps, telemetry overlay.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors, selector_two_drivers
from app.components.charts import delta_chart, telemetry_chart, telemetry_dashboard, speed_delta_chart, lap_time_chart
from src.data.fetch_fastf1 import load_session, get_all_laps, get_fastest_lap_telemetry
from src.analysis.pace_analysis import compute_pace_summary, compute_pace_gap, get_smoothed_laps
from src.analysis.telemetry_analysis import get_driver_telemetry_comparison, summarise_telemetry
from src.analysis.strategy_analysis import extract_stints
from ai.context_builder import build_driver_battle_context
from ai.groq_client import chat_completion
from ai.prompts import driver_battle_prompt
from utils.helpers import format_lap_time

configure_page("Driver Battle — Formula Insights AI")
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
year, gp, session_code = full_session_selectors()

with st.spinner("Loading session…"):
    try:
        session = load_session(year, gp, session_code)
        laps_raw = get_all_laps(session)
    except Exception as e:
        st.error(f"❌ {e}")
        st.stop()

driver_a, driver_b = selector_two_drivers(session)
st.sidebar.markdown("---")

page_header(
    f"{driver_a} vs {driver_b}",
    subtitle=f"{year} {gp} · Head-to-Head Analysis",
    badge="Driver Battle",
)

if not driver_a or not driver_b or driver_a == driver_b:
    st.warning("Please select two different drivers from the sidebar.")
    st.stop()

# ── Pace gap KPIs ─────────────────────────────────────────────────────────────
pace_df = compute_pace_summary(laps_raw)
gap_row = compute_pace_gap(laps_raw, driver_a, driver_b)

med_a, med_b = "—", "—"
if not pace_df.empty:
    for drv, col_name in [(driver_a, "med_a"), (driver_b, "med_b")]:
        row = pace_df[pace_df["Driver"] == drv]
        if not row.empty:
            val = format_lap_time(row.iloc[0]["MedianLapTime"])
            if col_name == "med_a":
                med_a = val
            else:
                med_b = val

pace_advantage = "—"
if not gap_row.empty and "PaceGap" in gap_row.columns:
    avg_gap = gap_row["PaceGap"].mean()
    sign = "+" if avg_gap > 0 else ""
    faster = driver_b if avg_gap > 0 else driver_a
    pace_advantage = f"{sign}{avg_gap:.3f}s ({faster} faster)"

kpi_row([
    ("Driver A", driver_a, f"Median: {med_a}"),
    ("Driver B", driver_b, f"Median: {med_b}"),
    ("Avg Pace Gap", pace_advantage, f"{driver_a} − {driver_b}"),
])
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["⏱️ Lap Times", "📉 Delta", "📡 Telemetry", "🤖 AI Analysis"])

# ── Tab 1: Lap Times ─────────────────────────────────────────────────────────
with tab1:
    section_header("Lap-by-Lap Comparison")
    smoothed = get_smoothed_laps(laps_raw, [driver_a, driver_b])
    if smoothed.empty:
        no_data_state()
    else:
        col = "LapTimeSmoothed" if "LapTimeSmoothed" in smoothed.columns else "LapTimeSeconds"
        fig = lap_time_chart(smoothed, [driver_a, driver_b], col=col,
                             title=f"Lap Times: {driver_a} vs {driver_b}")
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Delta ─────────────────────────────────────────────────────────────
with tab2:
    section_header("Lap-by-Lap Pace Delta")
    if gap_row.empty:
        no_data_state("Not enough laps to compute delta.")
    else:
        fig = delta_chart(gap_row, driver_a, driver_b,
                          title=f"Pace Delta: {driver_a} − {driver_b}")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw Delta Data"):
            st.dataframe(gap_row, use_container_width=True, hide_index=True)

# ── Tab 3: Telemetry ─────────────────────────────────────────────────────────
with tab3:
    section_header("Fastest Lap Telemetry Overlay")
    with st.spinner("Loading telemetry data…"):
        tel_a = get_fastest_lap_telemetry(session, driver_a)
        tel_b = get_fastest_lap_telemetry(session, driver_b)

    if tel_a.empty or tel_b.empty:
        no_data_state("Telemetry not available for one or both drivers.")
    else:
        compared = get_driver_telemetry_comparison(tel_a, tel_b, driver_a, driver_b)

        if compared:
            # Multi-channel dashboard
            tel_dict = {driver_a: compared["a"], driver_b: compared["b"]}
            channels = ["Speed", "Throttle", "Brake"]
            channels = [c for c in channels if c in compared["a"].columns]

            for channel in channels:
                fig = telemetry_chart(
                    tel_dict, channel=channel,
                    title=f"{channel} Trace — {driver_a} vs {driver_b}",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Speed delta
            if "delta" in compared and not compared["delta"].empty:
                section_header("Speed Delta")
                fig = speed_delta_chart(compared["delta"], driver_a, driver_b)
                st.plotly_chart(fig, use_container_width=True)

        # Telemetry stats side-by-side
        section_header("Telemetry Statistics")
        stats_a = summarise_telemetry(tel_a)
        stats_b = summarise_telemetry(tel_b)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{driver_a}**")
            for k, v in stats_a.items():
                st.markdown(f"- **{k.replace('_', ' ').title()}**: {v}")
        with c2:
            st.markdown(f"**{driver_b}**")
            for k, v in stats_b.items():
                st.markdown(f"- **{k.replace('_', ' ').title()}**: {v}")

# ── Tab 4: AI Analysis ────────────────────────────────────────────────────────
with tab4:
    section_header("AI Battle Analysis")
    stints = extract_stints(laps_raw)
    pace_gap_val, sector_deltas, strategy_diff = build_driver_battle_context(
        driver_a, driver_b, pace_df, stints
    )

    if st.button("🤖 Generate AI Battle Report", key="battle_ai"):
        with st.spinner("Analysing battle data…"):
            system, user = driver_battle_prompt(
                driver_a=driver_a,
                driver_b=driver_b,
                year=year,
                gp=gp,
                pace_gap=pace_gap_val,
                sector_deltas=sector_deltas,
                strategy_diff=strategy_diff,
            )
            result = chat_completion(system, user, max_tokens=900)
        # st.markdown(
        #     f'<div class="fi-chat-ai">{result}</div>',
        #     unsafe_allow_html=True,
        # )
        with st.container(border=True):
            st.markdown(result)
