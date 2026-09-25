"""Standardized structured logging for AgriRisk Kenya."""

import logging
import sys
from typing import Optional
from agririsk.core.config import settings


def get_logger(name: str = "agririsk", level: Optional[str] = None) -> logging.Logger:
    """Configure and return a standardized structured logger.

    Args:
        name: Name of the logger, typically __name__ or module identifier.
        level: Optional log level string override (e.g. DEBUG, INFO, WARNING).
    """
    logger = logging.getLogger(name)
    target_level = level or settings.log_level
    log_level_int = getattr(logging, target_level.upper(), logging.INFO)
    logger.setLevel(log_level_int)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level_int)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = get_logger()
