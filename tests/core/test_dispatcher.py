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


def test_price_config_rejects_unimplemented_backend() -> None:
    config_data = _valid_config()
    config_data.numerics.backend = "py_pde"

    with pytest.raises(PricingError, match="not implemented"):
        price_config(config_data)


def test_price_config_requires_spot_parameter() -> None:
    config_data = _valid_config()
    del config_data.process.parameters["S0"]

    with pytest.raises(PricingError, match="Missing spot level"):
        price_config(config_data)
