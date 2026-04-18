"""Typer CLI entrypoint for PDEAlchemy."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.core import price_config
from pdealchemy.exceptions import PDEAlchemyError, ValidationError
from pdealchemy.logging_config import configure_logging
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.notebook_spec import notebook_to_toml_file
from pdealchemy.render import render_explain_output
from pdealchemy.spec_bridge import (
    BlackScholesBridgeDefaults,
    spec_to_runtime_toml_file,
)
from pdealchemy.validation import ValidationRunner, validate_equation_library

app = typer.Typer(
    name="pdealchemy",
    help="PDEAlchemy CLI for option pricing, validation, and explain rendering.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


class ExplainFormat(StrEnum):
    """Output formats supported by the explain command."""

    MARKDOWN = "markdown"
    TEXT = "text"
    LATEX = "latex"


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", help="Enable info-level logging."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging and tracebacks."),
    json_logs: bool = typer.Option(False, "--json-logs", help="Emit logs in JSON format."),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="Optional path for structured JSON log output.",
    ),
) -> None:
    """Initialise logging configuration for all commands."""
    configure_logging(verbose=verbose, debug=debug, json_logs=json_logs, log_file=log_file)
    logger.debug("CLI initialised with verbose={} debug={}", verbose, debug)


@app.command()
def price(
    config_path: Path = typer.Argument(..., help="Path to a pricing TOML config file."),
) -> None:
    """Run the pricing workflow."""
    try:
        config_data = load_pricing_config(config_path)
        pricing_result = price_config(config_data)
        logger.info("Price command completed for {}", config_path)
        console.print(
            "[bold green]Pricing successful:[/bold green] "
            f"{pricing_result.price:.8f}\n"
            f"Backend: {pricing_result.backend}\n"
            f"Engine: {pricing_result.engine}"
        )
    except PDEAlchemyError as exc:
        console.print(exc.to_cli_message())
        raise typer.Exit(code=2) from exc


@app.command("notebook-to-toml")
def notebook_to_toml(
    notebook_path: Path = typer.Argument(..., help="Path to a marimo specification notebook."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output TOML file path. Defaults to notebook path with .toml suffix.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
) -> None:
    """Convert a marimo specification notebook into TOML."""
    try:
        output_path = notebook_to_toml_file(
            notebook_path,
            output_path=output,
            overwrite=overwrite,
        )
        console.print(
            f"[bold green]Notebook conversion successful:[/bold green] wrote `{output_path}`."
        )
    except PDEAlchemyError as exc:
        console.print(exc.to_cli_message())
        raise typer.Exit(code=2) from exc


@app.command("spec-to-runtime-toml")
def spec_to_runtime_toml(
    spec_path: Path = typer.Argument(..., help="Path to a specification TOML file."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output runtime TOML path. Defaults to <spec>.runtime.toml.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
    spot: float = typer.Option(100.0, "--spot", help="Spot level S0."),
    strike: float = typer.Option(100.0, "--strike", help="Strike K."),
    rate: float = typer.Option(0.05, "--rate", help="Constant risk-free rate r."),
    volatility: float = typer.Option(0.2, "--volatility", help="Constant volatility sigma."),
    maturity: float = typer.Option(1.0, "--maturity", help="Option maturity in years."),
    backend: str = typer.Option(
        "quantlib",
        "--backend",
        help="Runtime backend (`quantlib` or `py_pde`).",
    ),
    scheme: str = typer.Option("crank_nicolson", "--scheme", help="Numerical scheme."),
    time_steps: int = typer.Option(250, "--time-steps", help="Number of time steps."),
    damping_steps: int = typer.Option(0, "--damping-steps", help="Number of damping steps."),
    grid_lower: float = typer.Option(0.0, "--grid-lower", help="Lower grid bound for S."),
    grid_upper: float = typer.Option(400.0, "--grid-upper", help="Upper grid bound for S."),
    grid_points: int = typer.Option(401, "--grid-points", help="Grid points for S."),
) -> None:
    """Bridge a notebook specification TOML into executable runtime pricing TOML."""
    try:
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
        output_path = spec_to_runtime_toml_file(
            spec_path,
            output_path=output,
            overwrite=overwrite,
            defaults=defaults,
        )
        console.print(f"[bold green]Spec bridge successful:[/bold green] wrote `{output_path}`.")
    except PDEAlchemyError as exc:
        console.print(exc.to_cli_message())
        raise typer.Exit(code=2) from exc


@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Path to a TOML config file."),
    analytical: bool = typer.Option(
        False,
        "--analytical",
        help="Run the analytical Black-Scholes benchmark check when applicable.",
    ),
    tolerance: float = typer.Option(
        0.5,
        "--tolerance",
        min=0.0,
        help="Absolute error tolerance used with --analytical.",
    ),
    equation_library: Path | None = typer.Option(
        None,
        "--equation-library",
        help=(
            "Optional path to a Markdown equation library directory for constrained "
            "LaTeX validation."
        ),
    ),
) -> None:
    """Validate that the configuration file matches PDEAlchemy schema."""
    try:
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
        console.print(
            "[bold green]Validation successful:[/bold green] "
            f"{len(config_data.process.state_variables)} state variable(s), "
            f"backend `{config_data.numerics.backend}`."
            f"{validation_note}"
        )
    except PDEAlchemyError as exc:
        console.print(exc.to_cli_message())
        raise typer.Exit(code=2) from exc


@app.command()
def explain(
    config_path: Path = typer.Argument(..., help="Path to a TOML config file."),
    format: ExplainFormat = typer.Option(ExplainFormat.TEXT, "--format", help="Output format."),
) -> None:
    """Render a high-level description of the provided TOML config."""
    try:
        config_data = load_pricing_config(config_path)
        symbolic_problem = build_symbolic_problem(config_data)
        rendered = render_explain_output(
            config_data,
            symbolic_problem,
            output_format=format,
        )

        if format is ExplainFormat.MARKDOWN:
            console.print(Markdown(rendered))
        elif format is ExplainFormat.LATEX:
            console.print(Syntax(rendered, "latex", theme="ansi_dark"))
        else:
            console.print(rendered)
    except PDEAlchemyError as exc:
        console.print(exc.to_cli_message())
        raise typer.Exit(code=2) from exc


def main() -> None:
    """CLI script entrypoint."""
    app()


if __name__ == "__main__":
    main()
