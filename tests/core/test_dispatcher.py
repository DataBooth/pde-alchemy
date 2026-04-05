"""Tests for pricing dispatcher and QuantLib adapter."""

from __future__ import annotations

import pytest

from pdealchemy.config.models import PricingConfig
from pdealchemy.core import price_config
from pdealchemy.exceptions import PricingError


def _valid_config() -> PricingConfig:
    return PricingConfig.model_validate(
        {
            "metadata": {"name": "Dispatcher baseline"},
            "process": {
                "state_variables": ["S"],
                "parameters": {"S0": 100.0, "r": 0.05, "sigma": 0.2, "K": 100.0},
                "drift": {"S": "r * S"},
                "diffusion": {"S": "sigma * S"},
            },
            "instrument": {
                "kind": "vanilla_option",
                "payoff": "max(S - K, 0)",
                "maturity": 1.0,
                "exercise": "european",
                "style": "call",
            },
            "numerics": {
                "backend": "quantlib",
                "scheme": "crank_nicolson",
                "time_steps": 200,
                "damping_steps": 0,
                "grid": {
                    "lower": {"S": 0.0},
                    "upper": {"S": 400.0},
                    "points": {"S": 401},
                },
            },
        }
    )


def _exotic_config() -> PricingConfig:
    config_data = _valid_config().model_dump()
    config_data["instrument"]["kind"] = "exotic_option"
    config_data["features"] = {
        "barrier": {
            "type": "up_and_out",
            "level": 145.0,
            "rebate": 0.0,
        },
        "asian": {
            "averaging": "discrete_arithmetic",
            "observation_times": [0.25, 0.5, 0.75, 1.0],
        },
        "dividends": {
            "events": [
                {"time": 0.3, "amount": 0.75},
                {"time": 0.65, "amount": 0.75},
            ]
        },
    }
    config_data["numerics"]["monte_carlo"] = {
        "paths": 5000,
        "seed": 42,
        "antithetic": True,
    }
    return PricingConfig.model_validate(config_data)


def test_price_config_quantlib_returns_plausible_value() -> None:
    result = price_config(_valid_config())

    assert result.backend == "quantlib"
    assert result.engine == "FdBlackScholesVanillaEngine"
    assert result.price == pytest.approx(10.45, abs=1.0)


def test_price_config_exotic_combo_routes_to_monte_carlo() -> None:
    result = price_config(_exotic_config())

    assert result.backend == "quantlib"
    assert result.engine == "MonteCarloDiscreteAsianBarrierDividendEngine"
    assert result.price > 0.0


def test_price_config_py_pde_returns_plausible_value() -> None:
    config_data = _valid_config()
    config_data.numerics.backend = "py_pde"
    config_data.numerics.time_steps = 150
    config_data.numerics.grid.points["S"] = 241

    result = price_config(config_data)
    assert result.backend == "py_pde"
    assert result.engine == "CrankNicolsonBlackScholes1D"
    assert result.price == pytest.approx(10.45, abs=1.0)


def test_price_config_py_pde_rejects_exotic_features() -> None:
    config_data = _exotic_config()
    config_data.numerics.backend = "py_pde"

    with pytest.raises(PricingError, match="supports vanilla routes only"):
        price_config(config_data)


def test_price_config_requires_spot_parameter() -> None:
    config_data = _valid_config()
    del config_data.process.parameters["S0"]

    with pytest.raises(PricingError, match="Missing spot level"):
        price_config(config_data)


def test_price_config_vanilla_accepts_market_curve_and_surface() -> None:
    config_data = _valid_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.0],
            "rates": [0.03, 0.035],
        },
        "dividend_curve": {
            "kind": "flat",
            "rate": 0.01,
        },
        "volatility": {
            "kind": "surface",
            "times": [0.25, 1.0],
            "strikes": [90.0, 100.0, 110.0],
            "vols": [
                [0.24, 0.22, 0.21],
                [0.25, 0.23, 0.22],
            ],
        },
    }
    result = price_config(PricingConfig.model_validate(config_data))

    assert result.backend == "quantlib"
    assert result.engine == "FdBlackScholesVanillaEngine"
    assert result.price > 0.0
    assert result.metadata["rate_curve"] == "zero_curve"
    assert result.metadata["volatility_structure"] == "surface"


def test_price_config_exotic_rejects_non_flat_market_curve() -> None:
    config_data = _exotic_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.0],
            "rates": [0.03, 0.035],
        }
    }

    with pytest.raises(PricingError, match="supports flat market curves only"):
        price_config(PricingConfig.model_validate(config_data))
