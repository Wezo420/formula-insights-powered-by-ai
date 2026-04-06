"""
Centralised logger for Formula Insights AI.
Produces structured INFO / ERROR output to both console and rotating file.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGERS: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Return a named logger; create it once and cache."""
    if name in _LOGGERS:
        return _LOGGERS[name]

    # Import here to avoid circular deps at module load time
    from config.settings import LOG_LEVEL, LOG_DIR

    logger = logging.getLogger(name)
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Rotating file (5 MB × 3 backups)
    log_file = Path(LOG_DIR) / "formula_insights.log"
    fh = RotatingFileHandler(log_file, maxBytes=5_242_880, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    _LOGGERS[name] = logger
    return logger
