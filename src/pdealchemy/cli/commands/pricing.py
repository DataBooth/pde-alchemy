"""Pricing command execution logic."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.core import price_config


def run_price_command(config_path: Path) -> str:
    """Execute pricing workflow and return formatted rich message text."""
    config_data = load_pricing_config(config_path)
    pricing_result = price_config(config_data)
    logger.info("Price command completed for {}", config_path)
    return (
        "[bold green]Pricing successful:[/bold green] "
        f"{pricing_result.price:.8f}\n"
        f"Backend: {pricing_result.backend}\n"
        f"Engine: {pricing_result.engine}"
    )
