"""Typer CLI entrypoint for PDEAlchemy."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from pdealchemy.cli.commands import (
    run_explain_command,
    run_notebook_to_toml_command,
    run_price_command,
    run_spec_to_runtime_toml_command,
    run_validate_command,
)
from pdealchemy.exceptions import PDEAlchemyError
from pdealchemy.logging_config import configure_logging

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
        console.print(run_price_command(config_path))
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
        console.print(
            run_notebook_to_toml_command(
                notebook_path,
                output_path=output,
                overwrite=overwrite,
            )
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
        help="Output pricing TOML path. Defaults to <spec>.pricing.toml.",
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
        console.print(
            run_spec_to_runtime_toml_command(
                spec_path,
                output_path=output,
                overwrite=overwrite,
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
        )
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
        console.print(
            run_validate_command(
                config_path,
                analytical=analytical,
                tolerance=tolerance,
                equation_library=equation_library,
            )
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
        rendered = run_explain_command(config_path, output_format=format)

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
