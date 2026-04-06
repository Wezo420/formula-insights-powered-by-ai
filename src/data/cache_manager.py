"""
FastF1 cache manager.
Call `init_cache()` once before any FastF1 API calls.
"""
import fastf1
from config.settings import FASTF1_CACHE_DIR
from utils.logger import get_logger

log = get_logger(__name__)

_cache_initialised = False


def init_cache() -> None:
    """Enable FastF1 disk cache (idempotent)."""
    global _cache_initialised
    if _cache_initialised:
        return
    try:
        fastf1.Cache.enable_cache(str(FASTF1_CACHE_DIR))
        log.info("FastF1 cache enabled at %s", FASTF1_CACHE_DIR)
        _cache_initialised = True
    except Exception as exc:
        log.error("Failed to initialise FastF1 cache: %s", exc)
        raise


def clear_cache() -> None:
    """Remove all cached FastF1 files (use with caution)."""
    import shutil

    try:
        shutil.rmtree(str(FASTF1_CACHE_DIR))
        FASTF1_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        log.info("FastF1 cache cleared.")
    except Exception as exc:
        log.error("Failed to clear cache: %s", exc)
