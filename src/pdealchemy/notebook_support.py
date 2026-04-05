"""Utilities for marimo notebook examples."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.config.models import PricingConfig
from pdealchemy.core import PricingResult, price_config
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.render import render_explain_output
from pdealchemy.validation import ValidationOutcome, ValidationRunner

ExampleName = Literal["vanilla", "exotic"]


@dataclass(frozen=True)
class NotebookOutputs:
    """Structured outputs used by interactive notebooks."""

    pricing_result: PricingResult
    explain_markdown: str
    analytical_outcome: ValidationOutcome | None = None


def repository_root_from_notebook(notebook_file: Path) -> Path:
    """Resolve repository root from an examples/notebooks file path."""
    return notebook_file.resolve().parents[2]


def canonical_example_paths(repo_root: Path) -> dict[ExampleName, Path]:
    """Return canonical example config paths."""
    return {
        "vanilla": repo_root / "examples" / "vanilla_european_call.toml",
        "exotic": repo_root / "examples" / "exotic_discrete_asian_barrier_dividend.toml",
    }


def load_canonical_example(example_name: ExampleName, *, repo_root: Path) -> PricingConfig:
    """Load a canonical pricing config by short name."""
    example_paths = canonical_example_paths(repo_root)
    if example_name not in example_paths:
        raise ValueError(f"Unsupported example name: {example_name}")
    return load_pricing_config(example_paths[example_name])


def with_monte_carlo_paths(config_data: PricingConfig, paths: int) -> PricingConfig:
    """Return a copy of config with updated Monte Carlo path count."""
    config_copy = config_data.model_copy(deep=True)
    config_copy.numerics.monte_carlo.paths = paths
    return config_copy


def prepare_notebook_outputs(
    config_data: PricingConfig,
    *,
    run_analytical: bool = False,
    tolerance: float = 0.75,
) -> NotebookOutputs:
    """Run explain, price, and optionally analytical validation for notebooks."""
    symbolic_problem = build_symbolic_problem(config_data)
    explain_markdown = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="markdown",
    )
    pricing_result = price_config(config_data)

    analytical_outcome = None
    if run_analytical:
        runner = ValidationRunner()
        analytical_outcome = runner.run_analytical_black_scholes(
            config_data,
            tolerance=tolerance,
        )

    return NotebookOutputs(
        pricing_result=pricing_result,
        explain_markdown=explain_markdown,
        analytical_outcome=analytical_outcome,
    )
