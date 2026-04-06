"""
General-purpose helper utilities for Formula Insights AI.
"""
from __future__ import annotations

import time
import functools
from typing import Callable, Any, TypeVar

import pandas as pd
import numpy as np

from utils.logger import get_logger

log = get_logger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


# ── Retry with exponential backoff ────────────────────────────────────────────
def retry(max_attempts: int = 3, base_delay: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator: retry *func* up to *max_attempts* times with exponential back-off."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        log.error(
                            "All %d attempts failed for %s: %s",
                            max_attempts,
                            func.__name__,
                            exc,
                        )
                        raise
                    delay = base_delay ** attempt
                    log.warning(
                        "Attempt %d/%d for %s failed (%s). Retrying in %.1fs…",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                        delay,
                    )
                    time.sleep(delay)

        return wrapper  # type: ignore

    return decorator


# ── Lap time formatting ───────────────────────────────────────────────────────
def format_lap_time(seconds: float | None) -> str:
    """Convert raw seconds to M:SS.mmm string."""
    if seconds is None or pd.isna(seconds):
        return "N/A"
    try:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:06.3f}"
    except Exception:
        return "N/A"


def timedelta_to_seconds(td) -> float | None:
    """Convert pandas Timedelta / numpy timedelta64 to float seconds."""
    try:
        if pd.isna(td):
            return None
        if isinstance(td, pd.Timedelta):
            return td.total_seconds()
        if isinstance(td, np.timedelta64):
            return float(td) / 1e9
        return float(td)
    except Exception:
        return None


# ── Outlier removal ───────────────────────────────────────────────────────────
def remove_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Return *series* with IQR-based outliers replaced by NaN."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    mask = (series >= q1 - k * iqr) & (series <= q3 + k * iqr)
    return series.where(mask)


def smooth_series(series: pd.Series, window: int = 3) -> pd.Series:
    """Rolling mean smoothing, forward/back filled at edges."""
    return series.rolling(window, center=True, min_periods=1).mean()


# ── Driver / session helpers ──────────────────────────────────────────────────
def abbreviate_name(full_name: str) -> str:
    """'Max Verstappen' → 'VER'  (last 3 uppercase letters of surname)."""
    parts = full_name.strip().split()
    if not parts:
        return "UNK"
    return parts[-1][:3].upper()


def safe_divide(num: float, den: float, default: float = 0.0) -> float:
    """Division that never raises ZeroDivisionError."""
    return num / den if den != 0 else default


# ── Colour helpers ────────────────────────────────────────────────────────────
def get_driver_color(driver: str, session_drivers: list[str] | None = None) -> str:
    """
    Return a consistent hex colour per driver abbreviation.
    Falls back to a deterministic palette if no team colour is known.
    """
    palette = [
        "#3671C6", "#E8002D", "#27F4D2", "#FF8000", "#229971",
        "#FF87BC", "#64C4FF", "#6692FF", "#52E252", "#B6BABD",
        "#F0F0F0", "#FFC906", "#C92D4B", "#00A19C", "#FF6B35",
    ]
    if session_drivers:
        idx = session_drivers.index(driver) if driver in session_drivers else 0
        return palette[idx % len(palette)]
    return palette[hash(driver) % len(palette)]
