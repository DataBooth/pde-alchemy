"""Notebook and specification conversion command execution logic."""

from __future__ import annotations

from pathlib import Path

from pdealchemy.notebook_spec import notebook_to_toml_file
from pdealchemy.spec_bridge import BlackScholesBridgeDefaults, spec_to_runtime_toml_file


def run_notebook_to_toml_command(
    notebook_path: Path,
    *,
    output_path: Path | None,
    overwrite: bool,
) -> str:
    """Convert notebook specification source into TOML and return success message."""
    target_path = notebook_to_toml_file(
        notebook_path,
        output_path=output_path,
        overwrite=overwrite,
    )
    return f"[bold green]Notebook conversion successful:[/bold green] wrote `{target_path}`."


def run_spec_to_runtime_toml_command(
    spec_path: Path,
    *,
    output_path: Path | None,
    overwrite: bool,
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    backend: str,
    scheme: str,
    time_steps: int,
    damping_steps: int,
    grid_lower: float,
    grid_upper: float,
    grid_points: int,
) -> str:
    """Bridge specification TOML into pricing TOML and return success message."""
    defaults = BlackScholesBridgeDefaults(
        spot=spot,
        strike=strike,
        rate=rate,
        volatility=volatility,
        maturity=maturity,
        backend=backend,
        scheme=scheme,
        time_steps=time_steps,
        damping_steps=damping_steps,
        grid_lower=grid_lower,
        grid_upper=grid_upper,
        grid_points=grid_points,
    )
    target_path = spec_to_runtime_toml_file(
        spec_path,
        output_path=output_path,
        overwrite=overwrite,
        defaults=defaults,
    )
    return f"[bold green]Spec bridge successful:[/bold green] wrote `{target_path}`."
