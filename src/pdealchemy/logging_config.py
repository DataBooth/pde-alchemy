"""Central logging configuration for PDEAlchemy."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def configure_logging(
    *,
    verbose: bool = False,
    debug: bool = False,
    json_logs: bool = False,
    log_file: Path | None = None,
) -> None:
    """Configure global logging sinks."""
    logger.remove()

    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"

    logger.add(
        sys.stdout,
        level=log_level,
        serialize=json_logs,
        backtrace=debug,
        diagnose=debug,
        colorize=not json_logs,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        ),
    )

    if log_file is not None:
        logger.add(
            log_file,
            level=log_level,
            serialize=True,
            rotation="5 MB",
            retention=5,
            backtrace=debug,
            diagnose=debug,
        )
