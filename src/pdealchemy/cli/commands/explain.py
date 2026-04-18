"""Explain command execution logic."""

from __future__ import annotations

from pathlib import Path

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.render import render_explain_output


def run_explain_command(
    config_path: Path,
    *,
    output_format: str,
) -> str:
    """Render explain output for the requested format."""
    config_data = load_pricing_config(config_path)
    symbolic_problem = build_symbolic_problem(config_data)
    return render_explain_output(
        config_data,
        symbolic_problem,
        output_format=output_format,
    )
