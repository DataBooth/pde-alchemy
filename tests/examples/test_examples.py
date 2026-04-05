"""Tests for canonical example configurations."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy.config import load_pricing_config
from pdealchemy.core import price_config

REPO_ROOT = Path(__file__).resolve().parents[2]
VANILLA_EXAMPLE = REPO_ROOT / "examples" / "vanilla_european_call.toml"
EXOTIC_EXAMPLE = REPO_ROOT / "examples" / "exotic_discrete_asian_barrier_dividend.toml"
MARKET_EXAMPLE = REPO_ROOT / "examples" / "vanilla_market_curve_surface.toml"


@pytest.mark.parametrize("example_path", [VANILLA_EXAMPLE, EXOTIC_EXAMPLE, MARKET_EXAMPLE])
def test_examples_load(example_path: Path) -> None:
    config_data = load_pricing_config(example_path)
    assert config_data.instrument.maturity > 0.0


def test_vanilla_example_prices_successfully() -> None:
    config_data = load_pricing_config(VANILLA_EXAMPLE)
    result = price_config(config_data)

    assert result.price > 0.0
    assert result.engine == "FdBlackScholesVanillaEngine"


def test_exotic_example_prices_successfully() -> None:
    config_data = load_pricing_config(EXOTIC_EXAMPLE)
    config_data.numerics.monte_carlo.paths = 5000
    result = price_config(config_data)

    assert result.price > 0.0
    assert result.engine == "MonteCarloDiscreteAsianBarrierDividendEngine"


def test_market_example_prices_successfully() -> None:
    config_data = load_pricing_config(MARKET_EXAMPLE)
    result = price_config(config_data)

    assert result.price > 0.0
    assert result.engine == "FdBlackScholesVanillaEngine"
