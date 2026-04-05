"""Tests for analytical validation harness."""

from __future__ import annotations

import pytest

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import ValidationError
from pdealchemy.validation import ValidationRunner, black_scholes_price


def _valid_config() -> PricingConfig:
    return PricingConfig.model_validate(
        {
            "metadata": {"name": "Validation baseline"},
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


def test_black_scholes_call_reference_value() -> None:
    price = black_scholes_price(
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        option_style="call",
    )
    assert price == pytest.approx(10.45058, rel=1e-4)


def test_validation_runner_passes_with_reasonable_tolerance() -> None:
    runner = ValidationRunner()
    outcome = runner.run_analytical_black_scholes(_valid_config(), tolerance=0.75)

    assert outcome.passed
    assert outcome.absolute_error <= outcome.tolerance


def test_validation_runner_fails_with_strict_tolerance() -> None:
    runner = ValidationRunner()
    outcome = runner.run_analytical_black_scholes(_valid_config(), tolerance=1e-8)

    assert not outcome.passed
    assert outcome.absolute_error > outcome.tolerance


def test_validation_runner_rejects_exotic_features() -> None:
    config_data = _valid_config().model_dump()
    config_data["features"] = {
        "barrier": {"type": "up_and_out", "level": 145.0, "rebate": 0.0}
    }
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="only available for non-exotic configs"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))
