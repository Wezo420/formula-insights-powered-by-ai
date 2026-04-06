"""
Page 3 — Tyre Strategy
Stint visualisation, pit stop timeline, compound comparison, AI strategy analysis.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors, selector_drivers
from app.components.charts import strategy_chart, degradation_chart
from src.data.fetch_fastf1 import load_session, get_all_laps
from src.analysis.strategy_analysis import extract_stints, get_pit_stop_laps, get_compound_distribution
from src.analysis.degradation_analysis import compute_degradation_per_stint, project_degradation_curve
from ai.context_builder import build_strategy_context
from ai.groq_client import chat_completion
from ai.prompts import strategy_analysis_prompt

configure_page("Strategy — Formula Insights AI")
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

selected_drivers = selector_drivers(session, max_drivers=10)
st.sidebar.markdown("---")

page_header(
    "Tyre Strategy",
    subtitle=f"{year} {gp} · Stint & Compound Analysis",
    badge="Strategy",
)

if laps_raw.empty:
    no_data_state()
    st.stop()

# ── Compute ───────────────────────────────────────────────────────────────────
stints = extract_stints(laps_raw)
pit_laps = get_pit_stop_laps(laps_raw)
compound_dist = get_compound_distribution(laps_raw)
deg_df = compute_degradation_per_stint(laps_raw)

if selected_drivers:
    stints_display = stints[stints["Driver"].isin(selected_drivers)]
    pit_display = pit_laps[pit_laps["Driver"].isin(selected_drivers)] if not pit_laps.empty else pit_laps
else:
    stints_display = stints
    pit_display = pit_laps

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_pits = len(pit_display)
avg_stint = stints_display["StintLength"].mean() if not stints_display.empty else 0
n_compounds = compound_dist["Compound"].nunique() if not compound_dist.empty else 0

kpi_row([
    ("Pit Stops", str(total_pits), "In selected sample"),
    ("Avg Stint Length", f"{avg_stint:.1f}", "Laps per stint"),
    ("Compounds Used", str(n_compounds), "Across the race"),
])
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔄 Strategy Map", "🛑 Pit Stops", "📊 Compound Stats",
    "📉 Degradation", "🤖 AI Analysis",
])

# ── Tab 1: Strategy Map ───────────────────────────────────────────────────────
with tab1:
    section_header("Stint Visualisation")
    if stints_display.empty:
        no_data_state("No stint data available.")
    else:
        fig = strategy_chart(stints_display, title="Tyre Strategy — All Drivers")
        st.plotly_chart(fig, use_container_width=True)

        section_header("Stint Details")
        display = stints_display.copy()
        if "AvgLapTime" in display.columns:
            from utils.helpers import format_lap_time
            display["AvgLapTime"] = display["AvgLapTime"].apply(format_lap_time)
            display["BestLapTime"] = display["BestLapTime"].apply(format_lap_time)
        st.dataframe(display, use_container_width=True, hide_index=True)

# ── Tab 2: Pit Stops ─────────────────────────────────────────────────────────
with tab2:
    section_header("Pit Stop Timeline")
    if pit_display.empty:
        no_data_state("No pit stop data available.")
    else:
        st.dataframe(pit_display, use_container_width=True, hide_index=True)

        import plotly.graph_objects as go
        from config.settings import PLOTLY_TEMPLATE, COMPOUND_COLORS
        from utils.helpers import get_driver_color

        fig = go.Figure()
        pit_drivers = pit_display["Driver"].unique().tolist()
        for driver in pit_drivers:
            drv_pits = pit_display[pit_display["Driver"] == driver]
            color = get_driver_color(driver, pit_drivers)
            for _, row in drv_pits.iterrows():
                new_c = str(row.get("NewCompound", "UNKNOWN")).upper()
                fig.add_trace(go.Scatter(
                    x=[row["PitLap"]],
                    y=[driver],
                    mode="markers+text",
                    marker=dict(
                        size=18,
                        color=COMPOUND_COLORS.get(new_c, "#999"),
                        symbol="diamond",
                        line=dict(color="#fff", width=1.5),
                    ),
                    text=[new_c[0]],
                    textposition="middle center",
                    textfont=dict(color="#000", size=9, family="Barlow Condensed"),
                    name=driver,
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        f"Pit on Lap: {int(row['PitLap'])}<br>"
                        f"→ {new_c}<extra></extra>"
                    ),
                    showlegend=False,
                ))

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Lap Number",
            yaxis_title="Driver",
            height=max(300, len(pit_drivers) * 45 + 100),
            font=dict(family="Barlow"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: Compound Stats ────────────────────────────────────────────────────
with tab3:
    section_header("Compound Usage Distribution")
    if compound_dist.empty:
        no_data_state()
    else:
        import plotly.express as px
        dist_filtered = (
            compound_dist[compound_dist["Driver"].isin(selected_drivers)]
            if selected_drivers else compound_dist
        )
        from config.settings import COMPOUND_COLORS
        fig = px.bar(
            dist_filtered,
            x="Driver",
            y="LapCount",
            color="Compound",
            color_discrete_map=COMPOUND_COLORS,
            barmode="stack",
            title="Laps per Compound",
            template="plotly_dark",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 4: Degradation ────────────────────────────────────────────────────────
with tab4:
    section_header("Tyre Degradation Curves")
    if deg_df.empty:
        no_data_state("Not enough stint data to compute degradation.")
    else:
        st.dataframe(
            deg_df.style.format({
                "DegradationRate": "{:+.4f}s/lap",
                "R2": "{:.3f}",
                "BaseLapTime": "{:.3f}s",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        section_header("Select Stint to Visualise")

        plot_drivers = selected_drivers if selected_drivers else deg_df["Driver"].unique().tolist()[:3]
        deg_chart_data = {}
        for drv in plot_drivers:
            drv_stints = deg_df[deg_df["Driver"] == drv]
            if drv_stints.empty:
                continue
            stint_no = int(drv_stints.iloc[0]["StintNumber"])
            proj = project_degradation_curve(drv, laps_raw, stint_no, project_laps=8)
            if not proj.empty:
                deg_chart_data[drv] = proj

        if deg_chart_data:
            fig = degradation_chart(deg_chart_data, title="Degradation & Projection")
            st.plotly_chart(fig, use_container_width=True)
        else:
            no_data_state("Could not project degradation curves.")

# ── Tab 5: AI Analysis ────────────────────────────────────────────────────────
with tab5:
    section_header("AI Strategy Analysis")
    if st.button("🤖 Analyse Strategy with AI", key="strat_ai"):
        strategy_summary, degradation_summary = build_strategy_context(stints_display, deg_df)
        plot_drivers = selected_drivers if selected_drivers else list(stints_display["Driver"].unique())

        with st.spinner("Generating strategy analysis…"):
            system, user = strategy_analysis_prompt(
                year=year,
                gp=gp,
                drivers=plot_drivers,
                strategy_summary=strategy_summary,
                degradation_summary=degradation_summary,
            )
            result = chat_completion(system, user, max_tokens=1000)
        st.markdown(f'<div class="fi-chat-ai">{result}</div>', unsafe_allow_html=True)
