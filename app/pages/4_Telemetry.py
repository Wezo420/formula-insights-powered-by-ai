"""
Page 4 — Telemetry
Speed / throttle / brake / gear traces with mini-sector analysis.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors, selector_drivers
from app.components.charts import telemetry_dashboard, telemetry_chart, speed_delta_chart
from src.data.fetch_fastf1 import load_session, get_all_laps, get_fastest_lap_telemetry, get_lap_telemetry
from src.analysis.telemetry_analysis import (
    summarise_telemetry,
    compute_sector_mini_sectors,
    compute_braking_zones,
    get_driver_telemetry_comparison,
)
from config.settings import PLOTLY_TEMPLATE

configure_page("Telemetry — Formula Insights AI")
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
year, gp, session_code = full_session_selectors()
circuit_info = None
with st.spinner("Loading session…"):
    try:
        session = load_session(year, gp, session_code)
        laps_raw = get_all_laps(session)
    except Exception as e:
        st.error(f"❌ {e}")
        st.stop()

selected_drivers = selector_drivers(session, max_drivers=6)
st.sidebar.markdown("---")

# Lap mode selector
lap_mode = st.sidebar.radio(
    "Lap Selection",
    ["Fastest Lap", "Specific Lap"],
    key="tel_lap_mode",
)
specific_lap = None
if lap_mode == "Specific Lap":
    max_lap = int(laps_raw["LapNumber"].max()) if not laps_raw.empty else 70
    specific_lap = st.sidebar.number_input(
        "Lap Number", min_value=1, max_value=max_lap, value=10, key="tel_lap_no"
    )

page_header(
    "Telemetry Analysis",
    subtitle=f"{year} {gp} · {lap_mode}",
    badge="Telemetry",
)

plot_drivers = selected_drivers if selected_drivers else []
if not plot_drivers:
    st.info("Select at least one driver from the sidebar.")
    st.stop()

# ── Load telemetry ────────────────────────────────────────────────────────────
with st.spinner("Fetching telemetry…"):
    tel_data: dict[str, pd.DataFrame] = {}
    for drv in plot_drivers:
        try:
            if lap_mode == "Fastest Lap":
                tel = get_fastest_lap_telemetry(session, drv)
            else:
                tel = get_lap_telemetry(session, drv, int(specific_lap))
            if not tel.empty:
                tel_data[drv] = tel
        except Exception as e:
            st.warning(f"Telemetry unavailable for {drv}: {e}")

if not tel_data:
    no_data_state("No telemetry data available for the selected drivers / lap.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
# Show stats for first driver
first_drv = list(tel_data.keys())[0]
stats = summarise_telemetry(tel_data[first_drv])
kpi_row([
    ("Max Speed", f"{stats.get('max_speed', '—')} km/h", first_drv),
    ("Avg Speed", f"{stats.get('avg_speed', '—')} km/h", first_drv),
    ("Full Throttle", f"{stats.get('full_throttle_pct', '—')}%", "of lap"),
    ("Braking", f"{stats.get('braking_pct', '—')}%", "of lap"),
])
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Full Dashboard", "🚀 Speed", "🎛️ Throttle & Brake", "🏁 Mini Sectors"
])

# ── Tab 1: Full Dashboard ─────────────────────────────────────────────────────
with tab1:
    section_header("Telemetry Dashboard")
    channels = [c for c in ["Speed", "Throttle", "Brake", "nGear", "RPM"]
                if any(c in df.columns for df in tel_data.values())]

    if channels:
        fig = telemetry_dashboard(tel_data, channels=channels[:4])
        st.plotly_chart(fig, use_container_width=True)
    else:
        no_data_state("No telemetry channels found.")

# ── Tab 2: Speed ──────────────────────────────────────────────────────────────
with tab2:
    section_header("Speed Trace")
    fig = telemetry_chart(tel_data, channel="Speed", title="Speed vs Distance", circuit_info=circuit_info)
    st.plotly_chart(fig, use_container_width=True)

    # Speed delta if exactly 2 drivers
    if len(tel_data) == 2:
        drivers_list = list(tel_data.keys())
        d_a, d_b = drivers_list[0], drivers_list[1]
        compared = get_driver_telemetry_comparison(
            tel_data[d_a], tel_data[d_b], d_a, d_b
        )
        if compared and "delta" in compared and not compared["delta"].empty:
            section_header("Speed Delta")
            fig = speed_delta_chart(compared["delta"], d_a, d_b)
            st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: Throttle & Brake ──────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        section_header("Throttle Trace")
        fig = telemetry_chart(tel_data, channel="Throttle", title="Throttle Application", circuit_info=circuit_info)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        section_header("Brake Trace")
        fig = telemetry_chart(tel_data, channel="Brake", title="Brake Application", circuit_info=circuit_info)
        st.plotly_chart(fig, use_container_width=True)

    # Per-driver stats table
    section_header("Driver Telemetry Statistics")
    stats_rows = []
    for drv, df in tel_data.items():
        s = summarise_telemetry(df)
        stats_rows.append({"Driver": drv, **s})
    if stats_rows:
        st.dataframe(pd.DataFrame(stats_rows), use_container_width=True, hide_index=True)

# ── Tab 4: Mini Sectors ───────────────────────────────────────────────────────
with tab4:
    section_header("Mini-Sector Speed Analysis")
    st.caption(
        "The lap is divided into 20 equal-distance sectors. "
        "Average speed per sector shows where each driver gains or loses time."
    )

    mini_fig = go.Figure()
    for drv, df in tel_data.items():
        mini = compute_sector_mini_sectors(df, n_sectors=20)
        if mini.empty:
            continue
        from utils.helpers import get_driver_color
        color = get_driver_color(drv, list(tel_data.keys()))
        mini_fig.add_trace(go.Bar(
            x=mini["MiniSector"],
            y=mini["AvgSpeed"],
            name=drv,
            marker_color=color,
            opacity=0.85,
            hovertemplate=f"<b>{drv}</b><br>Sector %{{x}}<br>Avg Speed: %{{y:.1f}} km/h<extra></extra>",
        ))

    mini_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        xaxis_title="Mini Sector",
        yaxis_title="Avg Speed (km/h)",
        font=dict(family="Barlow"),
        legend=dict(bgcolor="rgba(17,17,24,0.8)"),
    )
    st.plotly_chart(mini_fig, use_container_width=True)

    # Braking zones for first driver
    section_header(f"Braking Zones — {first_drv}")
    braking_df = compute_braking_zones(tel_data[first_drv])
    if not braking_df.empty:
        st.dataframe(
            braking_df.style.format({
                "StartDist": "{:.0f}m",
                "EndDist": "{:.0f}m",
                "ZoneLength": "{:.0f}m",
                "MaxBrake": "{:.1f}%",
                "EntrySpeed": "{:.1f} km/h",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        no_data_state("Braking zone data not available.")
