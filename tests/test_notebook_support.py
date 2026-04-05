"""Tests for notebook support helpers."""

from __future__ import annotations

from pathlib import Path

from pdealchemy.notebook_support import (
    canonical_example_paths,
    load_canonical_example,
    prepare_notebook_outputs,
    repository_root_from_notebook,
    with_monte_carlo_paths,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_repository_root_from_notebook_path() -> None:
    notebook_file = _repo_root() / "examples" / "notebooks" / "price_explorer.py"
    resolved_root = repository_root_from_notebook(notebook_file)
    assert resolved_root == _repo_root()


def test_load_canonical_examples() -> None:
    example_paths = canonical_example_paths(_repo_root())
    vanilla = load_canonical_example("vanilla", repo_root=_repo_root())
    exotic = load_canonical_example("exotic", repo_root=_repo_root())

    assert example_paths["vanilla"].exists()
    assert example_paths["exotic"].exists()
    assert vanilla.instrument.kind == "vanilla_option"
    assert exotic.instrument.kind == "exotic_option"


def test_prepare_outputs_for_vanilla_with_analytical() -> None:
    config_data = load_canonical_example("vanilla", repo_root=_repo_root())
    outputs = prepare_notebook_outputs(config_data, run_analytical=True, tolerance=0.75)

    assert outputs.pricing_result.price > 0.0
    assert outputs.analytical_outcome is not None
    assert outputs.analytical_outcome.passed


def test_prepare_outputs_for_exotic_with_adjusted_paths() -> None:
    config_data = load_canonical_example("exotic", repo_root=_repo_root())
    config_data_small = with_monte_carlo_paths(config_data, 5000)
    outputs = prepare_notebook_outputs(config_data_small)

    assert outputs.pricing_result.price > 0.0
    assert outputs.pricing_result.engine == "MonteCarloDiscreteAsianBarrierDividendEngine"
