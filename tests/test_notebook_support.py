"""Tests for notebook support helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy.exceptions import PricingError
from pdealchemy.notebook_support import (
    apply_interactive_profile,
    canonical_example_dropdown_options,
    canonical_example_paths,
    default_canonical_example_label,
    load_canonical_example,
    prepare_notebook_outputs,
    repository_root_from_notebook,
    resolve_canonical_example_selection,
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

def test_canonical_example_dropdown_options_are_metadata_driven() -> None:
    options = canonical_example_dropdown_options(_repo_root())
    assert options["Vanilla European call baseline"] == "vanilla"
    assert options["Discrete Asian + barrier + dividend call"] == "exotic"


def test_default_canonical_example_label_prefers_vanilla() -> None:
    default_label = default_canonical_example_label(_repo_root())
    assert default_label == "Vanilla European call baseline"


def test_resolve_canonical_example_selection_accepts_label_and_id() -> None:
    assert (
        resolve_canonical_example_selection(
            "Vanilla European call baseline",
            repo_root=_repo_root(),
        )
        == "vanilla"
    )
    assert resolve_canonical_example_selection("exotic", repo_root=_repo_root()) == "exotic"


def test_resolve_canonical_example_selection_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unsupported example name"):
        resolve_canonical_example_selection("unknown", repo_root=_repo_root())


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


def test_prepare_outputs_for_vanilla_dual_backend_with_greeks_and_spot_sweep() -> None:
    config_data = load_canonical_example("vanilla", repo_root=_repo_root())
    outputs = prepare_notebook_outputs(
        config_data,
        backends=("quantlib", "py_pde"),
        include_greeks=True,
        include_spot_sweep=True,
        spot_sweep_points=5,
        include_convergence=True,
        convergence_points=4,
    )

    assert set(outputs.pricing_by_backend) == {"quantlib", "py_pde"}
    quantlib_price = outputs.pricing_by_backend["quantlib"].price
    py_pde_price = outputs.pricing_by_backend["py_pde"].price
    assert quantlib_price > 0.0
    assert py_pde_price > 0.0
    assert abs(quantlib_price - py_pde_price) < 1.0

    assert set(outputs.greeks_by_backend) == {"quantlib", "py_pde"}
    for backend_name in ("quantlib", "py_pde"):
        greek_values = outputs.greeks_by_backend[backend_name]
        assert set(greek_values) == {"delta", "gamma", "vega", "rho", "theta"}

    assert "spot" in outputs.spot_sweep
    assert len(outputs.spot_sweep["spot"]) == 5
    assert len(outputs.spot_sweep["quantlib:price"]) == 5
    assert len(outputs.spot_sweep["py_pde:price"]) == 5

    assert "time_steps" in outputs.convergence_sweep
    assert "space_steps" in outputs.convergence_sweep
    assert "mesh_size" in outputs.convergence_sweep
    assert len(outputs.convergence_sweep["time_steps"]) >= 3
    assert len(outputs.convergence_sweep["space_steps"]) == len(
        outputs.convergence_sweep["time_steps"]
    )
    assert len(outputs.convergence_sweep["mesh_size"]) == len(
        outputs.convergence_sweep["time_steps"]
    )
    assert all(mesh_size > 0.0 for mesh_size in outputs.convergence_sweep["mesh_size"])
    assert len(outputs.convergence_sweep["quantlib:price"]) == len(
        outputs.convergence_sweep["time_steps"]
    )
    assert len(outputs.convergence_sweep["py_pde:price"]) == len(
        outputs.convergence_sweep["time_steps"]
    )
    assert "backend_abs_diff" in outputs.convergence_sweep


def test_apply_interactive_profile_scales_runtime_parameters() -> None:
    config_data = load_canonical_example("vanilla", repo_root=_repo_root())

    fast = apply_interactive_profile(config_data, "fast")
    balanced = apply_interactive_profile(config_data, "balanced")
    accurate = apply_interactive_profile(config_data, "accurate")

    assert fast.numerics.time_steps <= balanced.numerics.time_steps
    assert balanced.numerics.time_steps <= accurate.numerics.time_steps
    assert fast.numerics.grid.points["S"] <= balanced.numerics.grid.points["S"]
    assert balanced.numerics.grid.points["S"] <= accurate.numerics.grid.points["S"]
    assert fast.numerics.monte_carlo.paths <= balanced.numerics.monte_carlo.paths
    assert balanced.numerics.monte_carlo.paths <= accurate.numerics.monte_carlo.paths


def test_prepare_outputs_rejects_py_pde_for_exotic() -> None:
    config_data = load_canonical_example("exotic", repo_root=_repo_root())

    with pytest.raises(PricingError, match="supports vanilla routes only"):
        prepare_notebook_outputs(config_data, backends=("py_pde",))
