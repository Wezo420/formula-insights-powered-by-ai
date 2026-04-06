"""
Page 5 — AI Insights
Ask any question about the race. AI answers with real data context.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st

from app.components.layout import configure_page, inject_css, page_header, section_header, no_data_state
from app.components.selectors import full_session_selectors, selector_drivers
from src.data.fetch_fastf1 import load_session, get_all_laps, get_race_results
from src.analysis.strategy_analysis import extract_stints
from ai.context_builder import build_race_context
from ai.groq_client import chat_completion
from ai.prompts import ai_insights_prompt, chatbot_prompt

configure_page("AI Insights — Formula Insights AI")
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

selected_drivers = selector_drivers(session, max_drivers=20)
st.sidebar.markdown("---")

page_header(
    "AI Insights",
    subtitle=f"{year} {gp} · AI-powered Q&A",
    badge="AI Insights",
)

# ── Build context ─────────────────────────────────────────────────────────────
stints = extract_stints(laps_raw)
race_context = build_race_context(laps_raw, results, stints, year, gp)

# ── Preset questions ──────────────────────────────────────────────────────────
PRESET_QUESTIONS = [
    f"Who had the best race pace and why?",
    f"Which strategy worked best in this race?",
    f"Who managed their tyres the most effectively?",
    f"What were the key moments that decided the race?",
    f"How did track position affect the outcome?",
    f"Who gained the most positions during the race?",
    f"What was the undercut / overcut situation?",
    f"How did the safety car (if any) impact strategies?",
]

# ── Mode selector ─────────────────────────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["💡 Quick Insights", "❓ Custom Question", "💬 Chat History"],
    horizontal=True,
    key="ai_mode",
)

st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

if mode == "💡 Quick Insights":
    section_header("Preset Race Questions")
    st.caption("Click any question for an instant AI-powered answer.")

    cols = st.columns(2)
    for i, q in enumerate(PRESET_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"preset_{i}", use_container_width=True):
                with st.spinner("Analysing…"):
                    system, user = ai_insights_prompt(year, gp, race_context, q)
                    answer = chat_completion(system, user, max_tokens=800)
                st.session_state[f"preset_answer_{i}"] = answer

            # Show answer if available
            answer_key = f"preset_answer_{i}"
            if answer_key in st.session_state:
                st.markdown(
                    f'<div class="fi-chat-ai" style="font-size:0.85rem;">'
                    f'{st.session_state[answer_key]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

elif mode == "❓ Custom Question":
    section_header("Ask the AI Analyst")

    question = st.text_area(
        "Your question",
        placeholder=f"e.g. Why was {selected_drivers[0] if selected_drivers else 'VER'} so much faster on the medium compound?",
        height=100,
        key="ai_custom_q",
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        ask = st.button("🤖 Analyse", key="ai_ask", use_container_width=True)
    with c2:
        include_context = st.toggle("Show data context used", value=False)

    if ask and question.strip():
        with st.spinner("Thinking…"):
            system, user = ai_insights_prompt(year, gp, race_context, question)
            answer = chat_completion(system, user, max_tokens=1000)
        st.markdown(
            f'<div class="fi-chat-ai">{answer}</div>',
            unsafe_allow_html=True,
        )
        if include_context:
            with st.expander("Data context provided to AI"):
                st.text(race_context)
    elif ask:
        st.warning("Please enter a question.")

elif mode == "💬 Chat History":
    section_header("Multi-turn AI Chat")
    st.caption("Context-aware conversation about this race session.")

    # Initialise chat history
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Render history
    for msg in st.session_state.ai_chat_history:
        role_class = "fi-chat-user" if msg["role"] == "user" else "fi-chat-ai"
        icon = "👤" if msg["role"] == "user" else "🤖"
        st.markdown(
            f'<div class="{role_class}">'
            f'<strong>{icon} {msg["role"].title()}</strong><br>{msg["content"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Input
    user_msg = st.chat_input("Ask about the race…")
    if user_msg:
        st.session_state.ai_chat_history.append({"role": "user", "content": user_msg})

        # Build prompt with history
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in st.session_state.ai_chat_history[-6:]
        )
        augmented_q = f"Conversation so far:\n{history_text}\n\nLatest question: {user_msg}"

        with st.spinner("Thinking…"):
            system, user = chatbot_prompt(year, gp, race_context, augmented_q)
            answer = chat_completion(system, user, max_tokens=700)

        st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.ai_chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.ai_chat_history = []
            st.rerun()
