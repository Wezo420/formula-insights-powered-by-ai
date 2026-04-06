"""
Central configuration for Formula Insights AI.
Loads environment variables and exposes typed settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Root paths ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ── App metadata ─────────────────────────────────────────────────────────────
APP_TITLE: str = os.getenv("APP_TITLE", "Formula Insights AI")
APP_ICON: str = os.getenv("APP_ICON", "🏎️")
APP_VERSION: str = "1.0.0"

# ── FastF1 ────────────────────────────────────────────────────────────────────
FASTF1_CACHE_DIR: Path = ROOT_DIR / os.getenv("FASTF1_CACHE_DIR", "data_cache")
FASTF1_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Groq AI ───────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"
GROQ_MAX_TOKENS: int = 2048
GROQ_TEMPERATURE: float = 0.7
GROQ_TIMEOUT: int = 30

# ── Retry / backoff ───────────────────────────────────────────────────────────
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0   # seconds

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Race data defaults ────────────────────────────────────────────────────────
DEFAULT_YEAR: int = 2024
DEFAULT_GP: str = "Bahrain"
DEFAULT_SESSION: str = "R"   # R = Race, Q = Qualifying

# ── UI ────────────────────────────────────────────────────────────────────────
PLOTLY_TEMPLATE: str = "plotly_dark"
TEAM_COLORS: dict[str, str] = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
}

COMPOUND_COLORS: dict[str, str] = {
    "SOFT": "#FF3333",
    "MEDIUM": "#FFF200",
    "HARD": "#EBEBEB",
    "INTERMEDIATE": "#39B54A",
    "WET": "#0067FF",
    "UNKNOWN": "#999999",
    "TEST_UNKNOWN": "#999999",
}

# ── Available seasons ─────────────────────────────────────────────────────────
AVAILABLE_YEARS: list[int] = list(range(2018, 2025))
