"""Utilities for marimo notebook examples."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.config.models import ConstantVolatilityConfig, FlatRateCurveConfig, PricingConfig
from pdealchemy.core import PricingResult, price_config
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.render import render_explain_output
from pdealchemy.validation import ValidationOutcome, ValidationRunner

ExampleName = Literal["vanilla", "exotic"]
BackendName = Literal["quantlib", "py_pde"]

_DEFAULT_GREEK_SPOT_BUMP_RELATIVE = 0.01
_DEFAULT_GREEK_RATE_BUMP_ABSOLUTE = 1e-4
_DEFAULT_GREEK_VOL_BUMP_ABSOLUTE = 1e-3


@dataclass(frozen=True)
class NotebookOutputs:
    """Structured outputs used by interactive notebooks."""

    pricing_result: PricingResult
    pricing_by_backend: dict[str, PricingResult]
    explain_markdown: str
    analytical_outcome: ValidationOutcome | None = None
    greeks_by_backend: dict[str, dict[str, float]] = field(default_factory=dict)
    spot_sweep: dict[str, list[float]] = field(default_factory=dict)


def _config_with_backend(config_data: PricingConfig, backend: BackendName) -> PricingConfig:
    config_copy = config_data.model_copy(deep=True)
    config_copy.numerics.backend = backend
    return config_copy


def _config_with_faster_numerics(config_data: PricingConfig) -> PricingConfig:
    """Return a copy with reduced numerical resolution for interactive sensitivity runs."""
    config_copy = config_data.model_copy(deep=True)
    config_copy.numerics.time_steps = min(config_copy.numerics.time_steps, 150)
    if "S" in config_copy.numerics.grid.points:
        config_copy.numerics.grid.points["S"] = min(config_copy.numerics.grid.points["S"], 241)
    return config_copy


def _spot_parameter_name(config_data: PricingConfig) -> str:
    parameters = config_data.process.parameters
    if "S0" in parameters:
        return "S0"
    if "spot" in parameters:
        return "spot"
    raise ValueError("Config does not define S0 or spot.")


def _config_with_spot(config_data: PricingConfig, spot_value: float) -> PricingConfig:
    config_copy = config_data.model_copy(deep=True)
    parameter_name = _spot_parameter_name(config_copy)
    config_copy.process.parameters[parameter_name] = spot_value
    return config_copy


def _config_with_rate(config_data: PricingConfig, risk_free_rate: float) -> PricingConfig:
    config_copy = config_data.model_copy(deep=True)
    config_copy.process.parameters["r"] = risk_free_rate
    if (
        config_copy.market is not None
        and isinstance(config_copy.market.risk_free_curve, FlatRateCurveConfig)
    ):
        config_copy.market.risk_free_curve.rate = risk_free_rate
    return config_copy


def _config_with_volatility(config_data: PricingConfig, volatility: float) -> PricingConfig:
    config_copy = config_data.model_copy(deep=True)
    config_copy.process.parameters["sigma"] = volatility
    if (
        config_copy.market is not None
        and isinstance(config_copy.market.volatility, ConstantVolatilityConfig)
    ):
        config_copy.market.volatility.vol = volatility
    return config_copy


def _config_with_maturity(config_data: PricingConfig, maturity: float) -> PricingConfig:
    config_copy = config_data.model_copy(deep=True)
    config_copy.instrument.maturity = maturity
    return config_copy


def _price_with_backend(config_data: PricingConfig, backend: BackendName) -> PricingResult:
    return price_config(_config_with_backend(config_data, backend))


def _finite_difference_greeks(
    config_data: PricingConfig,
    *,
    backend: BackendName,
) -> dict[str, float]:
    fast_config = _config_with_faster_numerics(config_data)
    base_result = _price_with_backend(fast_config, backend)
    base_price = base_result.price

    spot_name = _spot_parameter_name(fast_config)
    spot = fast_config.process.parameters[spot_name]
    spot_bump = max(abs(spot) * _DEFAULT_GREEK_SPOT_BUMP_RELATIVE, 1e-4)
    spot_down = max(spot - spot_bump, 1e-8)
    spot_up = spot + spot_bump

    price_up = _price_with_backend(_config_with_spot(fast_config, spot_up), backend).price
    price_down = _price_with_backend(_config_with_spot(fast_config, spot_down), backend).price
    denominator = max(spot_up - spot_down, 1e-12)
    delta = (price_up - price_down) / denominator
    gamma = (price_up - 2.0 * base_price + price_down) / ((0.5 * denominator) ** 2)

    sigma = fast_config.process.parameters["sigma"]
    vol_bump = min(_DEFAULT_GREEK_VOL_BUMP_ABSOLUTE, max(sigma * 0.2, 1e-5))
    sigma_down = max(sigma - vol_bump, 1e-8)
    sigma_up = sigma + vol_bump
    vega_up = _price_with_backend(_config_with_volatility(fast_config, sigma_up), backend).price
    vega_down = _price_with_backend(_config_with_volatility(fast_config, sigma_down), backend).price
    vega = (vega_up - vega_down) / max(sigma_up - sigma_down, 1e-12)

    rate = fast_config.process.parameters["r"]
    rate_bump = _DEFAULT_GREEK_RATE_BUMP_ABSOLUTE
    rho_up = _price_with_backend(_config_with_rate(fast_config, rate + rate_bump), backend).price
    rho_down = _price_with_backend(_config_with_rate(fast_config, rate - rate_bump), backend).price
    rho = (rho_up - rho_down) / (2.0 * rate_bump)

    maturity = fast_config.instrument.maturity
    maturity_bump = min(max(maturity * 0.02, 1e-4), 1.0 / 252.0)
    maturity_up_price = _price_with_backend(
        _config_with_maturity(fast_config, maturity + maturity_bump),
        backend,
    ).price
    theta = -(maturity_up_price - base_price) / maturity_bump

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "rho": rho,
        "theta": theta,
    }


def _spot_sweep(
    config_data: PricingConfig,
    *,
    backend: BackendName,
    points: int,
) -> tuple[list[float], list[float]]:
    if points < 3:
        raise ValueError("spot sweep requires at least three points.")

    fast_config = _config_with_faster_numerics(config_data)
    spot_name = _spot_parameter_name(fast_config)
    base_spot = fast_config.process.parameters[spot_name]
    spot_values = [
        base_spot * (0.7 + 0.6 * index / (points - 1))
        for index in range(points)
    ]
    prices = [
        _price_with_backend(_config_with_spot(fast_config, spot_value), backend).price
        for spot_value in spot_values
    ]
    return spot_values, prices


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
    backends: tuple[BackendName, ...] | None = None,
    include_greeks: bool = False,
    include_spot_sweep: bool = False,
    spot_sweep_points: int = 9,
) -> NotebookOutputs:
    """Run explain, price, and optionally analytical validation for notebooks."""
    symbolic_problem = build_symbolic_problem(config_data)
    explain_markdown = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="markdown",
    )

    selected_backends: tuple[BackendName, ...] = (
        backends if backends is not None else (config_data.numerics.backend,)
    )
    deduplicated_backends: tuple[BackendName, ...] = tuple(dict.fromkeys(selected_backends))
    pricing_by_backend: dict[str, PricingResult] = {
        str(backend): _price_with_backend(config_data, backend)
        for backend in deduplicated_backends
    }
    primary_backend = (
        config_data.numerics.backend
        if config_data.numerics.backend in pricing_by_backend
        else deduplicated_backends[0]
    )
    pricing_result = pricing_by_backend[primary_backend]

    analytical_outcome = None
    if run_analytical:
        runner = ValidationRunner()
        analytical_outcome = runner.run_analytical_black_scholes(
            config_data,
            tolerance=tolerance,
        )

    greeks_by_backend: dict[str, dict[str, float]] = {}
    if include_greeks:
        greeks_by_backend = {
            str(backend): _finite_difference_greeks(config_data, backend=backend)
            for backend in deduplicated_backends
        }

    spot_sweep: dict[str, list[float]] = {}
    if include_spot_sweep:
        spot_values: list[float] | None = None
        for backend in deduplicated_backends:
            backend_spots, backend_prices = _spot_sweep(
                config_data,
                backend=backend,
                points=spot_sweep_points,
            )
            if spot_values is None:
                spot_values = backend_spots
            spot_sweep[f"{backend}:price"] = backend_prices
        if spot_values is not None:
            spot_sweep["spot"] = spot_values

    return NotebookOutputs(
        pricing_result=pricing_result,
        pricing_by_backend=pricing_by_backend,
        explain_markdown=explain_markdown,
        analytical_outcome=analytical_outcome,
        greeks_by_backend=greeks_by_backend,
        spot_sweep=spot_sweep,
    )
