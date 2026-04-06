"""
Layout and styling components.
Injects the dark F1-themed CSS and provides shared UI building blocks.
"""
from __future__ import annotations

import streamlit as st
from config.settings import APP_TITLE, APP_ICON


DARK_CSS = """
<style>
  /* ── Google Fonts ──────────────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;800&family=Barlow:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

  /* ── Root variables ────────────────────────────────────────────── */
  :root {
    --bg-deep:    #0a0a0f;
    --bg-card:    #111118;
    --bg-hover:   #1a1a26;
    --accent:     #e10600;      /* F1 red */
    --accent2:    #ff6b35;      /* orange */
    --text-primary:   #f0f0f5;
    --text-secondary: #8888a8;
    --border:     rgba(255,255,255,0.07);
    --grid-line:  rgba(255,255,255,0.04);
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body:    'Barlow', sans-serif;
    --font-mono:    'JetBrains Mono', monospace;
    --radius:     6px;
  }

  /* ── Global reset ──────────────────────────────────────────────── */
  html, body, [class*="css"] {
    background-color: var(--bg-deep) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
  }

  /* ── Main container ─────────────────────────────────────────────── */
  .main .block-container {
    padding: 1.5rem 2.5rem 3rem !important;
    max-width: 1400px !important;
  }

  /* ── Sidebar ────────────────────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: #0d0d14 !important;
    border-right: 1px solid var(--border) !important;
  }
  section[data-testid="stSidebar"] * {
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stMultiSelect label {
    color: var(--text-secondary) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
  }

  /* ── Headings ───────────────────────────────────────────────────── */
  h1, h2, h3, h4 {
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
  }
  h1 { font-size: 2.4rem !important; color: var(--text-primary) !important; }
  h2 { font-size: 1.7rem !important; color: var(--text-primary) !important; }
  h3 { font-size: 1.25rem !important; color: var(--text-secondary) !important; }

  /* ── Cards / metric containers ──────────────────────────────────── */
  div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.2rem !important;
  }
  div[data-testid="metric-container"] label {
    color: var(--text-secondary) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
  }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
  }

  /* ── Buttons ────────────────────────────────────────────────────── */
  .stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-display) !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.4rem !important;
    transition: background 0.2s, transform 0.1s !important;
  }
  .stButton > button:hover {
    background: #c00400 !important;
    transform: translateY(-1px) !important;
  }

  /* ── Select / multiselect ───────────────────────────────────────── */
  .stSelectbox > div > div,
  .stMultiSelect > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
  }

  /* ── Text input ─────────────────────────────────────────────────── */
  .stTextInput > div > div > input,
  .stTextArea textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
  }

  /* ── Tabs ───────────────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-display) !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.2rem !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
  }
  .stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
  }

  /* ── Expanders ──────────────────────────────────────────────────── */
  details {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 0.5rem 1rem !important;
  }

  /* ── Dividers ───────────────────────────────────────────────────── */
  hr {
    border-color: var(--border) !important;
  }

  /* ── Spinner ────────────────────────────────────────────────────── */
  .stSpinner > div {
    border-top-color: var(--accent) !important;
  }

  /* ── Plotly charts: transparent bg ─────────────────────────────── */
  .js-plotly-plot .plotly {
    background: transparent !important;
  }

  /* ── Custom classes ─────────────────────────────────────────────── */
  .fi-badge {
    display: inline-block;
    background: var(--accent);
    color: #fff;
    font-family: var(--font-display);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 2px;
    margin-bottom: 0.5rem;
  }

  .fi-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
  }

  .fi-kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
  }
  .fi-kpi-card .label {
    font-family: var(--font-display);
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .fi-kpi-card .value {
    font-family: var(--font-display);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.1;
  }
  .fi-kpi-card .sub {
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin-top: 2px;
  }

  .fi-section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border);
  }
  .fi-section-header .title {
    font-family: var(--font-display);
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  .fi-section-header .accent-bar {
    width: 3px;
    height: 24px;
    background: var(--accent);
    border-radius: 2px;
  }

  /* ── Chat messages ──────────────────────────────────────────────── */
  .fi-chat-user {
    background: rgba(225, 6, 0, 0.08);
    border: 1px solid rgba(225, 6, 0, 0.2);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: var(--font-body);
  }
  .fi-chat-ai {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: var(--font-body);
    line-height: 1.7;
  }

  /* ── Scrollbar ──────────────────────────────────────────────────── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg-deep); }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
</style>
"""

def inject_css() -> None:
    """Inject the global dark-theme CSS into the Streamlit app."""
    st.markdown(DARK_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", badge: str = "") -> None:
    badge_html = f'<div class="fi-badge">{badge}</div>' if badge else ""
    sub_html = f'<p style="color:var(--text-secondary);font-size:0.9rem;margin:0.25rem 0 0;">{subtitle}</p>' if subtitle else ""
    html = badge_html + f'<h1 style="margin:0;line-height:1.1;">{title}</h1>' + sub_html + '<div style="height:1.5rem;"></div>'
    st.markdown(html, unsafe_allow_html=True)

def section_header(title: str) -> None:
    html = '<div class="fi-section-header"><div class="accent-bar"></div>' + f'<span class="title">{title}</span></div>'
    st.markdown(html, unsafe_allow_html=True)

def kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return f'<div class="fi-kpi-card"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

def kpi_row(cards: list[tuple[str, str, str]]) -> None:
    html = '<div class="fi-kpi-grid">'
    for label, value, sub in cards:
        html += kpi_card(label, value, sub)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def no_data_state(message: str = "No data available for the selected parameters.") -> None:
    html = (
        '<div style="text-align:center;padding:3rem 1rem;color:var(--text-secondary);'
        'border:1px dashed var(--border);border-radius:var(--radius);margin:1rem 0;">'
        '<div style="font-size:2rem;margin-bottom:0.5rem;">📡</div>'
        '<div style="font-family:var(--font-display);font-size:1rem;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.08em;">{message}</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

def configure_page(title: str = "Formula Insights AI", icon: str = "🏎️") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")

# def inject_css() -> None:
#     """Inject the global dark-theme CSS into the Streamlit app."""
#     st.markdown(DARK_CSS, unsafe_allow_html=True)


# def page_header(title: str, subtitle: str = "", badge: str = "") -> None:
#     """Render a styled page header with optional badge and subtitle."""
#     badge_html = (
#         f'<div class="fi-badge">{badge}</div>' if badge else ""
#     )
#     sub_html = (
#         f'<p style="color:var(--text-secondary);font-size:0.9rem;margin:0.25rem 0 0;">{subtitle}</p>'
#         if subtitle
#         else ""
#     )
#     st.markdown(
#         f"""
#         {badge_html}
#         <h1 style="margin:0;line-height:1.1;">{title}</h1>
#         {sub_html}
#         <div style="height:1.5rem;"></div>
#         """,
#         unsafe_allow_html=True,
#     )


# def section_header(title: str) -> None:
#     """Render a section header with accent bar."""
#     st.markdown(
#         f"""
#         <div class="fi-section-header">
#           <div class="accent-bar"></div>
#           <span class="title">{title}</span>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def kpi_card(label: str, value: str, sub: str = "") -> str:
#     """Return HTML for a single KPI card."""
#     return f"""
#     <div class="fi-kpi-card">
#       <div class="label">{label}</div>
#       <div class="value">{value}</div>
#       {"<div class='sub'>" + sub + "</div>" if sub else ""}
#     </div>
#     """


# def kpi_row(cards: list[tuple[str, str, str]]) -> None:
#     """
#     Render a responsive row of KPI cards.
#     Each card is (label, value, sub).
#     """
#     html = '<div class="fi-kpi-grid">'
#     for label, value, sub in cards:
#         html += kpi_card(label, value, sub)
#     html += "</div>"
#     st.markdown(html, unsafe_allow_html=True)


# def no_data_state(message: str = "No data available for the selected parameters.") -> None:
#     """Show a friendly no-data placeholder."""
#     st.markdown(
#         f"""
#         <div style="
#           text-align:center;padding:3rem 1rem;
#           color:var(--text-secondary);
#           border:1px dashed var(--border);
#           border-radius:var(--radius);
#           margin:1rem 0;
#         ">
#           <div style="font-size:2rem;margin-bottom:0.5rem;">📡</div>
#           <div style="font-family:var(--font-display);font-size:1rem;font-weight:600;
#                       text-transform:uppercase;letter-spacing:0.08em;">
#             {message}
#           </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def configure_page(title: str = APP_TITLE, icon: str = APP_ICON) -> None:
#     """Call once per page to set Streamlit page config."""
#     st.set_page_config(
#         page_title=title,
#         page_icon=icon,
#         layout="wide",
#         initial_sidebar_state="expanded",
#     )
