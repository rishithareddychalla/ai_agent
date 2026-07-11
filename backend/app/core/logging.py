"""
Centralized Logging Configuration using Loguru
"""

import sys
import os
from loguru import logger
from app.core.config import settings


def setup_logging():
    """Configure application-wide logging."""
    logger.remove()  # Remove default handler

    # Console handler with color
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="DEBUG" if settings.APP_ENV == "development" else "INFO",
        colorize=True,
    )

    # File handler
    log_file = os.path.join(settings.LOGS_DIR, "webpilot_{time:YYYY-MM-DD}.log")
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="gz",
    )

    logger.info("WebPilot AI logging configured")
