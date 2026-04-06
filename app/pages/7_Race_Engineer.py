"""
Page 7 — AI Race Engineer
Interactive telemetry-aware race engineer assistant with streaming responses.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st

from app.components.layout import configure_page, inject_css, page_header, section_header, kpi_row, no_data_state
from app.components.selectors import full_session_selectors, selector_single_driver
from app.components.charts import telemetry_chart, degradation_chart
from src.data.fetch_fastf1 import load_session, get_all_laps, get_race_results, get_fastest_lap_telemetry
from src.analysis.telemetry_analysis import summarise_telemetry
from src.analysis.degradation_analysis import compute_degradation_per_stint, project_degradation_curve
from src.analysis.strategy_analysis import extract_stints
from ai.race_engineer import get_driver_debrief, race_engineer_stream_response, suggest_questions

configure_page("Race Engineer — Formula Insights AI")
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

selected_driver = selector_single_driver(session, label="Driver to Engineer")
st.sidebar.markdown("---")

# Compound selector
compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
if not laps_raw.empty and "Compound" in laps_raw.columns:
    driver_compounds = laps_raw[laps_raw["Driver"] == selected_driver]["Compound"].dropna().unique().tolist()
    compounds = driver_compounds if driver_compounds else compounds

selected_compound = st.sidebar.selectbox(
    "Active Compound",
    options=compounds,
    index=0,
    key="eng_compound",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        font-size:0.72rem;color:#8888a8;
        font-family:'Barlow Condensed',sans-serif;
        letter-spacing:0.06em;text-transform:uppercase;
        margin-top:0.5rem;
    ">
        💡 Tips<br>
    </div>
    <div style="font-size:0.75rem;color:#666680;margin-top:0.3rem;line-height:1.5;">
        Ask about braking points, corner speed, tyre management, or sector times.
        The engineer has full access to telemetry and race data.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    f"Race Engineer — {selected_driver}",
    subtitle=f"{year} {gp} · AI Pitwall Debrief",
    badge="Race Engineer",
)

if not selected_driver:
    st.info("Select a driver from the sidebar.")
    st.stop()

# ── Load driver data ──────────────────────────────────────────────────────────
with st.spinner(f"Loading {selected_driver} data…"):
    telemetry = get_fastest_lap_telemetry(session, selected_driver)
    stints = extract_stints(laps_raw)
    deg_df = compute_degradation_per_stint(laps_raw)

# ── KPIs ──────────────────────────────────────────────────────────────────────
driver_laps = laps_raw[laps_raw["Driver"] == selected_driver] if not laps_raw.empty else None
tel_stats = summarise_telemetry(telemetry) if not telemetry.empty else {}

best_lap = "—"
if driver_laps is not None and not driver_laps.empty and "LapTimeSeconds" in driver_laps.columns:
    from utils.helpers import format_lap_time
    best_lap = format_lap_time(driver_laps["LapTimeSeconds"].min())

kpi_row([
    ("Driver", selected_driver, f"{year} {gp}"),
    ("Best Lap", best_lap, selected_compound),
    ("Max Speed", f"{tel_stats.get('max_speed', '—')} km/h", "Fastest lap"),
    ("Full Throttle", f"{tel_stats.get('full_throttle_pct', '—')}%", "of lap"),
])

st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎙️ Engineer Chat", "📋 Full Debrief", "📊 Performance Data"])

# ── Tab 1: Chat ───────────────────────────────────────────────────────────────
with tab1:
    section_header("Pitwall Chat")

    # Initialise conversation
    chat_key = f"eng_chat_{year}_{gp}_{selected_driver}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Suggested questions
    if not st.session_state[chat_key]:
        section_header("Suggested Questions")
        suggestions = suggest_questions(selected_driver, gp)
        cols = st.columns(2)
        for i, q in enumerate(suggestions[:6]):
            with cols[i % 2]:
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    st.session_state[chat_key].append({"role": "user", "content": q})
                    st.rerun()

    # Render history
    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="fi-chat-user"><strong>👤 You</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="fi-chat-ai"><strong>🎙️ Race Engineer</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # Chat input
    user_input = st.chat_input(f"Ask your race engineer about {selected_driver}…")
    if user_input:
        st.session_state[chat_key].append({"role": "user", "content": user_input})

        # Stream response
        response_placeholder = st.empty()
        full_response = ""

        with st.spinner("Engineer analysing data…"):
            for token in race_engineer_stream_response(
                driver=selected_driver,
                year=year,
                gp=gp,
                laps=laps_raw,
                results=results,
                stints=stints,
                telemetry=telemetry,
                conversation_history=st.session_state[chat_key][:-1],
                user_message=user_input,
            ):
                full_response += token
                response_placeholder.markdown(
                    f'<div class="fi-chat-ai"><strong>🎙️ Race Engineer</strong><br>{full_response}▋</div>',
                    unsafe_allow_html=True,
                )

        response_placeholder.markdown(
            f'<div class="fi-chat-ai"><strong>🎙️ Race Engineer</strong><br>{full_response}</div>',
            unsafe_allow_html=True,
        )
        st.session_state[chat_key].append({"role": "assistant", "content": full_response})

    if st.session_state[chat_key]:
        if st.button("🗑️ Clear Chat", key="eng_clear"):
            st.session_state[chat_key] = []
            st.rerun()

# ── Tab 2: Full Debrief ───────────────────────────────────────────────────────
with tab2:
    section_header("AI Performance Debrief")

    debrief_focus = st.selectbox(
        "Debrief Focus",
        [
            "Overall performance debrief",
            "Tyre management analysis",
            "Braking and trail-braking technique",
            "Throttle application and traction",
            "Sector-by-sector breakdown",
            "Strategy execution review",
        ],
        key="debrief_focus",
    )

    if st.button("🤖 Generate Full Debrief", key="gen_debrief", use_container_width=False):
        with st.spinner("Generating comprehensive debrief…"):
            debrief = get_driver_debrief(
                driver=selected_driver,
                year=year,
                gp=gp,
                laps=laps_raw,
                telemetry=telemetry,
                compound=selected_compound,
                question=debrief_focus,
            )
        st.session_state[f"debrief_{year}_{gp}_{selected_driver}"] = debrief

    debrief_cache_key = f"debrief_{year}_{gp}_{selected_driver}"
    if debrief_cache_key in st.session_state:
        with st.container(border=True):
            st.markdown(st.session_state[debrief_cache_key])
    else:
        st.info("Click 'Generate Full Debrief' to produce a comprehensive performance analysis.")

# ── Tab 3: Performance Data ───────────────────────────────────────────────────
with tab3:
    section_header("Telemetry Overview")

    if telemetry.empty:
        no_data_state("Telemetry data not available.")
    else:
        tel_dict = {selected_driver: telemetry}
        for channel in ["Speed", "Throttle", "Brake"]:
            if channel in telemetry.columns:
                fig = telemetry_chart(tel_dict, channel=channel,
                                      title=f"{channel} — Fastest Lap")
                st.plotly_chart(fig, use_container_width=True)

    section_header("Tyre Degradation")
    drv_deg = deg_df[deg_df["Driver"] == selected_driver] if not deg_df.empty else None
    if drv_deg is not None and not drv_deg.empty:
        st.dataframe(
            drv_deg.style.format({
                "DegradationRate": "{:+.4f} s/lap",
                "R2": "{:.3f}",
                "BaseLapTime": "{:.3f}s",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Degradation curve
        deg_chart_data = {}
        for _, row in drv_deg.iterrows():
            proj = project_degradation_curve(
                selected_driver, laps_raw, int(row["StintNumber"]), project_laps=6
            )
            if not proj.empty:
                deg_chart_data[f"Stint {int(row['StintNumber'])}"] = proj

        if deg_chart_data:
            fig = degradation_chart(
                deg_chart_data,
                title=f"{selected_driver} — Degradation Curves",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        no_data_state("Not enough data to model degradation.")
