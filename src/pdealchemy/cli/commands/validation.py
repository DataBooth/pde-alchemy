"""Validation command execution logic."""

from __future__ import annotations

from pathlib import Path

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.exceptions import ValidationError
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.validation import ValidationRunner, validate_equation_library


def run_validate_command(
    config_path: Path,
    *,
    analytical: bool,
    tolerance: float,
    equation_library: Path | None,
) -> str:
    """Validate configuration and return formatted rich summary text."""
    config_data = load_pricing_config(config_path)
    _ = build_symbolic_problem(config_data)
    validation_note = ""
    if analytical:
        runner = ValidationRunner()
        outcome = runner.run_analytical_black_scholes(
            config_data,
            tolerance=tolerance,
        )
        if not outcome.passed:
            raise ValidationError(
                "Analytical benchmark failed tolerance check.",
                details=(
                    f"model={outcome.model_price:.8f}, "
                    f"benchmark={outcome.benchmark_price:.8f}, "
                    f"abs_error={outcome.absolute_error:.8f}, "
                    f"tolerance={outcome.tolerance:.8f}"
                ),
                suggestion="Relax --tolerance or review model and numerical settings.",
            )
        validation_note = (
            f"\nAnalytical benchmark: passed "
            f"(abs error {outcome.absolute_error:.8f} <= {outcome.tolerance:.8f})"
        )
    if equation_library is not None:
        equation_summary = validate_equation_library(equation_library)
        validation_note += (
            f"\nEquation library: validated {equation_summary.equation_blocks_validated} "
            f"equation block(s) across {equation_summary.files_scanned} file(s)"
        )
    return (
        "[bold green]Validation successful:[/bold green] "
        f"{len(config_data.process.state_variables)} state variable(s), "
        f"backend `{config_data.numerics.backend}`."
        f"{validation_note}"
    )
