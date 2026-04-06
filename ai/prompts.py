"""
Centralised prompt templates for all AI features.
Each function returns a (system_prompt, user_prompt) tuple.
"""
from __future__ import annotations


# ── System personas ────────────────────────────────────────────────────────────
_RACE_ENGINEER_SYSTEM = """You are an elite Formula 1 race engineer with 20+ years of experience 
at top-tier teams. You analyse telemetry data, driving technique, and race strategy with 
surgical precision. Your feedback is technical, concise, and actionable — like a real 
pitwall debrief. You reference specific corners, braking points, throttle traces, and 
lap-time deltas. You never give vague answers."""

_ANALYST_SYSTEM = """You are a world-class Formula 1 performance analyst with expertise in 
data science, race strategy, and tyre compounds. You explain complex racing data in clear, 
engaging language. You always back your conclusions with numbers from the data provided. 
You structure your responses with clear headings and bullet points where appropriate."""

_SUMMARISER_SYSTEM = """You are an expert Formula 1 journalist and analyst who writes 
compelling, fact-driven race reports. Your writing is punchy, technically accurate, and 
captures the drama of the race. You structure reports with clear sections: key moments, 
strategy calls, driver performances, and a verdict."""

_CHATBOT_SYSTEM = """You are a knowledgeable Formula 1 AI assistant with deep expertise 
in race strategy, technical regulations, historical data, and driver performance. 
You use the provided race data context to give precise, insightful answers. 
When data is available, always reference specific numbers. Be concise but thorough."""


# ── Race Engineer prompts ──────────────────────────────────────────────────────
def race_engineer_feedback(
    driver: str,
    gp: str,
    year: int,
    telemetry_stats: dict,
    lap_times: list[float],
    compound: str,
    question: str,
) -> tuple[str, str]:
    user = f"""
Race: {year} {gp} Grand Prix
Driver: {driver}
Tyre Compound: {compound}

Telemetry Summary:
- Max Speed: {telemetry_stats.get('max_speed', 'N/A')} km/h
- Avg Speed: {telemetry_stats.get('avg_speed', 'N/A')} km/h
- Full Throttle: {telemetry_stats.get('full_throttle_pct', 'N/A')}% of lap
- Braking: {telemetry_stats.get('braking_pct', 'N/A')}% of lap
- Avg Gear: {telemetry_stats.get('avg_gear', 'N/A')}

Recent Lap Times (seconds): {[round(lt, 3) for lt in lap_times[-10:]]}

Driver Question / Focus Area:
{question}

Provide a detailed, data-driven race engineer debrief for this driver.
"""
    return _RACE_ENGINEER_SYSTEM, user


def race_engineer_chat(
    driver: str,
    gp: str,
    year: int,
    context: str,
    conversation_history: list[dict],
    user_message: str,
) -> tuple[str, str]:
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation_history[-6:]
    )
    user = f"""
Race Context: {year} {gp} Grand Prix | Driver: {driver}

Data Summary:
{context}

Conversation History:
{history_text}

Current Question: {user_message}
"""
    return _RACE_ENGINEER_SYSTEM, user


# ── Race Summariser prompts ───────────────────────────────────────────────────
def race_summary_prompt(
    year: int,
    gp: str,
    winner: str,
    top5: list[str],
    key_stats: dict,
    strategy_notes: str,
) -> tuple[str, str]:
    user = f"""
Generate a comprehensive race report for:

Race: {year} {gp} Grand Prix
Winner: {winner}
Top 5: {', '.join(top5)}

Key Race Statistics:
- Total Laps: {key_stats.get('total_laps', 'N/A')}
- Fastest Lap: {key_stats.get('fastest_lap_time', 'N/A')} by {key_stats.get('fastest_lap_driver', 'N/A')}
- Safety Cars: {key_stats.get('safety_cars', 'Unknown')}
- Lead Changes: {key_stats.get('lead_changes', 'Unknown')}

Strategy Overview:
{strategy_notes}

Structure your report as:
1. **Race Overview** — The story of the race
2. **Key Moments** — Decisive events lap by lap
3. **Strategy Analysis** — Who got it right and why
4. **Driver of the Day** — Best individual performance
5. **Verdict** — What this result means for the championship
"""
    return _SUMMARISER_SYSTEM, user


# ── AI Insights prompts ────────────────────────────────────────────────────────
def ai_insights_prompt(
    year: int,
    gp: str,
    context: str,
    question: str,
) -> tuple[str, str]:
    user = f"""
Race: {year} {gp} Grand Prix

Available Data:
{context}

Analyst Question: {question}

Provide a detailed, data-driven answer with specific references to the numbers above.
Structure with clear sections if the answer is complex.
"""
    return _ANALYST_SYSTEM, user


# ── Driver Battle prompt ───────────────────────────────────────────────────────
def driver_battle_prompt(
    driver_a: str,
    driver_b: str,
    year: int,
    gp: str,
    pace_gap: float,
    sector_deltas: dict,
    strategy_diff: str,
) -> tuple[str, str]:
    user = f"""
Analyse the head-to-head battle between {driver_a} and {driver_b}:

Race: {year} {gp}
Average Pace Gap: {pace_gap:+.3f}s ({driver_a} vs {driver_b})

Sector Deltas (positive = {driver_a} faster):
- Sector 1: {sector_deltas.get('s1', 'N/A')}s
- Sector 2: {sector_deltas.get('s2', 'N/A')}s
- Sector 3: {sector_deltas.get('s3', 'N/A')}s

Strategy Difference:
{strategy_diff}

Explain:
1. Where each driver gained/lost time
2. The decisive sector and why
3. How strategy impacted the battle
4. Who had the upper hand and why
"""
    return _ANALYST_SYSTEM, user


# ── Tyre Strategy prompt ───────────────────────────────────────────────────────
def strategy_analysis_prompt(
    year: int,
    gp: str,
    drivers: list[str],
    strategy_summary: str,
    degradation_summary: str,
) -> tuple[str, str]:
    user = f"""
Analyse the tyre strategies for: {year} {gp}

Drivers analysed: {', '.join(drivers)}

Strategy Details:
{strategy_summary}

Tyre Degradation:
{degradation_summary}

Explain:
1. Which strategy was optimal and why
2. Key degradation differences between compounds
3. Undercut / overcut opportunities
4. What the teams got right or wrong
"""
    return _ANALYST_SYSTEM, user


# ── Chatbot prompt ─────────────────────────────────────────────────────────────
def chatbot_prompt(
    year: int,
    gp: str,
    context: str,
    question: str,
) -> tuple[str, str]:
    user = f"""
Race: {year} {gp} Grand Prix

Race Data Context:
{context}

User Question: {question}

Answer precisely, referencing the data above where relevant.
"""
    return _CHATBOT_SYSTEM, user
