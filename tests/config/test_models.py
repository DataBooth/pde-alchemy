"""Unit tests for configuration schema models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdealchemy.config.models import PricingConfig


def _valid_config() -> dict[str, object]:
    return {
        "metadata": {"name": "Baseline 1D run"},
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


def test_pricing_config_accepts_valid_data() -> None:
    config_data = PricingConfig.model_validate(_valid_config())
    assert config_data.instrument.kind == "vanilla_option"
    assert config_data.numerics.backend == "quantlib"


def test_process_rejects_duplicate_state_variables() -> None:
    invalid = _valid_config()
    invalid["process"]["state_variables"] = ["S", "S"]  # type: ignore[index]

    with pytest.raises(ValidationError, match="state_variables must be unique"):
        PricingConfig.model_validate(invalid)


def test_grid_keys_must_match_state_variables() -> None:
    invalid = _valid_config()
    invalid["numerics"]["grid"]["upper"] = {"X": 400.0}  # type: ignore[index]

    with pytest.raises(ValidationError, match="numerics.grid.upper keys must match"):
        PricingConfig.model_validate(invalid)


def test_grid_bounds_require_lower_less_than_upper() -> None:
    invalid = _valid_config()
    invalid["numerics"]["grid"]["lower"] = {"S": 400.0}  # type: ignore[index]
    invalid["numerics"]["grid"]["upper"] = {"S": 200.0}  # type: ignore[index]

    with pytest.raises(ValidationError, match="must satisfy lower < upper"):
        PricingConfig.model_validate(invalid)


def test_rejects_asian_observation_time_beyond_maturity() -> None:
    invalid = _valid_config()
    invalid["features"] = {
        "asian": {
            "averaging": "discrete_arithmetic",
            "observation_times": [0.5, 1.5],
        }
    }

    with pytest.raises(
        ValidationError,
        match="asian.observation_times must be <= instrument.maturity",
    ):
        PricingConfig.model_validate(invalid)


def test_rejects_dividend_time_beyond_maturity() -> None:
    invalid = _valid_config()
    invalid["features"] = {
        "dividends": {
            "events": [
                {"time": 1.2, "amount": 0.5},
            ]
        }
    }

    with pytest.raises(
        ValidationError,
        match="dividends.events.time must be <= instrument.maturity",
    ):
        PricingConfig.model_validate(invalid)


def test_accepts_market_curve_and_surface_config() -> None:
    valid = _valid_config()
    valid["market"] = {
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

    config_data = PricingConfig.model_validate(valid)
    assert config_data.market is not None
    assert config_data.market.risk_free_curve is not None
    assert config_data.market.volatility is not None


def test_rejects_surface_shape_mismatch() -> None:
    invalid = _valid_config()
    invalid["market"] = {
        "volatility": {
            "kind": "surface",
            "times": [0.25, 1.0],
            "strikes": [90.0, 100.0, 110.0],
            "vols": [
                [0.24, 0.22],
                [0.25, 0.23],
            ],
        }
    }

    with pytest.raises(
        ValidationError,
        match="surface vols column count must match the number of surface strikes",
    ):
        PricingConfig.model_validate(invalid)


def test_rejects_market_curve_time_beyond_maturity() -> None:
    invalid = _valid_config()
    invalid["market"] = {
        "risk_free_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.2],
            "rates": [0.03, 0.035],
        }
    }

    with pytest.raises(
        ValidationError,
        match="market.risk_free_curve.times must be <= instrument.maturity",
    ):
        PricingConfig.model_validate(invalid)
