"""
Formula Insights AI — Entry Point
Run with:  streamlit run app/main.py
"""
import sys
import os

# ── Ensure project root is on sys.path so all imports resolve ─────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from app.components.layout import configure_page, inject_css
from app.components.selectors import sidebar_logo, full_session_selectors
from src.data.cache_manager import init_cache
from config.settings import APP_TITLE, APP_ICON

# ── Page config (must be first Streamlit call) ────────────────────────────────
configure_page(APP_TITLE, APP_ICON)
inject_css()

# ── Initialise FastF1 cache ───────────────────────────────────────────────────
try:
    init_cache()
except Exception as e:
    st.error(f"Cache init failed: {e}")

# ── Hero landing page ─────────────────────────────────────────────────────────
sidebar_logo()

st.markdown(
    """
    <div style="
        text-align:center;
        padding:4rem 2rem 3rem;
        background:linear-gradient(180deg, rgba(225,6,0,0.05) 0%, rgba(0,0,0,0) 100%);
        border-bottom:1px solid rgba(255,255,255,0.06);
        margin-bottom:3rem;
    ">
        <div style="
            font-family:'Barlow Condensed',sans-serif;
            font-size:4.5rem;
            font-weight:800;
            letter-spacing:0.04em;
            line-height:1;
            color:#f0f0f5;
            text-transform:uppercase;
        ">
            FORMULA <span style="color:#e10600;">INSIGHTS</span> AI
        </div>
        <div style="
            font-family:'Barlow',sans-serif;
            font-size:1.1rem;
            color:#8888a8;
            margin-top:0.8rem;
            letter-spacing:0.08em;
            text-transform:uppercase;
        ">
            End-to-End Formula 1 Analytics &amp; AI Platform
        </div>
        <div style="
            display:flex;justify-content:center;gap:1rem;margin-top:2rem;
            flex-wrap:wrap;
        ">
            <span style="
                background:rgba(225,6,0,0.12);border:1px solid rgba(225,6,0,0.3);
                color:#e10600;padding:4px 14px;border-radius:4px;
                font-family:'Barlow Condensed',sans-serif;font-size:0.78rem;
                font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
            ">FastF1 Powered</span>
            <span style="
                background:rgba(39,244,210,0.08);border:1px solid rgba(39,244,210,0.2);
                color:#27F4D2;padding:4px 14px;border-radius:4px;
                font-family:'Barlow Condensed',sans-serif;font-size:0.78rem;
                font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
            ">Groq AI</span>
            <span style="
                background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                color:#f0f0f5;padding:4px 14px;border-radius:4px;
                font-family:'Barlow Condensed',sans-serif;font-size:0.78rem;
                font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
            ">Real Telemetry</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Feature grid ──────────────────────────────────────────────────────────────
features = [
    ("📊", "Race Overview", "Full race story: results, fastest laps, key battles, and race pace evolution."),
    ("⚔️", "Driver Battle", "Corner-by-corner head-to-head comparison with delta time analysis."),
    ("🔄", "Tyre Strategy", "Stint visualisation, pit stop analysis, and compound comparison."),
    ("📡", "Telemetry", "Speed traces, throttle/brake maps, gear shifts — full car data overlay."),
    ("🤖", "AI Insights", "Ask any question about the race. AI-powered analysis with real data context."),
    ("📰", "Race Summary", "Auto-generated race report with key moments, strategy calls, and verdict."),
    ("🎙️", "Race Engineer", "Interactive AI race engineer — debrief, feedback, and coaching."),
]

cols = st.columns(3)
for i, (icon, name, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div style="
                background:#111118;border:1px solid rgba(255,255,255,0.07);
                border-radius:6px;padding:1.4rem;margin-bottom:1rem;
                transition:border-color 0.2s;
            ">
                <div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="
                    font-family:'Barlow Condensed',sans-serif;
                    font-size:1rem;font-weight:700;
                    color:#f0f0f5;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:0.4rem;
                ">{name}</div>
                <div style="font-size:0.83rem;color:#8888a8;line-height:1.5;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Getting started ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center;padding:1.5rem 0 0.5rem;">
        <div style="
            font-family:'Barlow Condensed',sans-serif;
            font-size:1.1rem;font-weight:700;
            color:#8888a8;text-transform:uppercase;letter-spacing:0.1em;
        ">
            ← Select a session in the sidebar, then navigate to any page
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
