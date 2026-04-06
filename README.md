# 🏎️ Formula Insights AI

> **End-to-End Formula 1 Analytics & AI Platform**
> Built with FastF1 · Streamlit · Plotly · Groq AI

---

## Overview

Formula Insights AI is a production-grade, full-stack analytics platform that transforms raw Formula 1 telemetry and session data into deep performance insights — augmented by a large language model race engineer.

Every feature follows the core pipeline:

```
DATA → ANALYSIS → VISUALIZATION → INSIGHT → AI EXPLANATION
```

---

## Features

### 📊 Race Overview
- Full race classification and results
- Smoothed lap time evolution for all drivers
- Pace distribution (violin plots)
- Cumulative gap to any reference driver

### ⚔️ Driver Battle
- Head-to-head lap time and delta comparison
- Fastest lap telemetry overlay (speed, throttle, brake)
- Speed delta trace (distance-aligned)
- AI-generated battle analysis

### 🔄 Tyre Strategy
- Colour-coded stint visualisation (Gantt-style)
- Pit stop timeline with compound changes
- Compound usage distribution
- Tyre degradation modeling with linear regression
- Degradation curves with lap-forward projection
- AI strategy analysis

### 📡 Telemetry
- Full multi-channel telemetry dashboard (speed, throttle, brake, gear, RPM)
- Mini-sector speed analysis (20 equal-distance zones)
- Braking zone identification and characterisation
- Multi-driver overlay on same distance axis
- Fastest lap or specific lap selection

### 🤖 AI Insights
- 8 preset race questions answered instantly
- Custom free-form question input
- Multi-turn context-aware chat
- All answers grounded in real session data

### 📰 Race Summary
- AI-generated full race report
  - Race overview and narrative
  - Key moments lap-by-lap
  - Strategy analysis
  - Driver of the Day
  - Championship verdict
- Race classification table
- Top 10 pace chart

### 🎙️ Race Engineer
- Interactive pitwall debrief chat (streaming responses)
- Suggested coaching questions
- Full AI performance debrief
- Telemetry charts per driver
- Per-stint degradation curves

---

## Architecture

```
formula-insights-ai/
├── app/
│   ├── main.py                  # Entry point & landing page
│   ├── pages/
│   │   ├── 1_Overview.py
│   │   ├── 2_Driver_Battle.py
│   │   ├── 3_Strategy.py
│   │   ├── 4_Telemetry.py
│   │   ├── 5_AI_Insights.py
│   │   ├── 6_Race_Summary.py
│   │   └── 7_Race_Engineer.py
│   └── components/
│       ├── selectors.py         # Sidebar UI components
│       ├── charts.py            # Plotly chart factories
│       └── layout.py            # CSS, theming, layout helpers
├── src/
│   ├── data/
│   │   ├── fetch_fastf1.py      # Primary data layer
│   │   └── cache_manager.py     # FastF1 cache initialisation
│   ├── processing/
│   │   ├── clean_data.py        # Outlier removal, data cleaning
│   │   └── feature_engineering.py  # Stint info, smoothing, deltas
│   └── analysis/
│       ├── pace_analysis.py     # Lap time stats and comparisons
│       ├── strategy_analysis.py # Stint extraction, pit stops
│       ├── telemetry_analysis.py# Telemetry processing
│       └── degradation_analysis.py  # Tyre deg modeling
├── ai/
│   ├── groq_client.py           # Groq API client (retry, streaming)
│   ├── prompts.py               # All prompt templates
│   ├── context_builder.py       # Race context serialisation
│   ├── summarizer.py            # Race report generator
│   └── race_engineer.py         # Engineer chat + debrief
├── config/
│   └── settings.py              # Central config (env vars, constants)
├── utils/
│   ├── logger.py                # Rotating file + console logging
│   └── helpers.py               # Retry decorator, formatters, colours
├── data_cache/                  # FastF1 cache (auto-created)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data source | FastF1 3.x |
| Web framework | Streamlit 1.40 |
| Charts | Plotly 5.x |
| AI / LLM | Groq (llama-3.3-70b-versatile) |
| Data processing | Pandas, NumPy, SciPy |
| Styling | Custom dark CSS (Barlow Condensed font) |
| Logging | Python `logging` + RotatingFileHandler |
| Config | python-dotenv |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourname/formula-insights-ai.git
cd formula-insights-ai
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 5. Run the application

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage

1. **Select a session** using the sidebar: pick a year, Grand Prix, and session type (Race, Qualifying, etc.)
2. **Navigate** to any page using the left sidebar
3. **Select drivers** as prompted on each page
4. **Click AI buttons** to generate insights (requires Groq API key)

> **Note:** The first load of any session downloads data from FastF1. This may take 30–60 seconds. Subsequent loads use the local disk cache and are near-instant.

---

## Reliability Features

- **Exponential backoff retry** on all AI API calls (3 attempts)
- **Rate limit detection** with graceful user messages
- **Timeout handling** on Groq API requests
- **FastF1 disk cache** to avoid redundant downloads
- **Streamlit `st.cache_data`** to prevent recomputation in the same session
- **IQR outlier removal** on lap time data
- **Try/except everywhere** — no crashes reach the user
- **Fallback AI responses** when the API is unavailable
- **Structured logging** to console + rotating file

---

## Configuration

All settings are in `config/settings.py` and can be overridden via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Required for AI features |
| `FASTF1_CACHE_DIR` | `data_cache` | FastF1 cache directory |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `APP_TITLE` | `Formula Insights AI` | Browser tab title |

---
