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
    config_data["features"] = {"barrier": {"type": "up_and_out", "level": 145.0, "rebate": 0.0}}
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="only available for non-exotic configs"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_rejects_non_flat_market_structure() -> None:
    config_data = _valid_config().model_dump()
    config_data["market"] = {
        "volatility": {
            "kind": "term_curve",
            "times": [0.25, 1.0],
            "vols": [0.2, 0.22],
        }
    }
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires constant market.volatility"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_rejects_non_s_state_variable() -> None:
    config_data = _valid_config().model_dump()
    config_data["process"]["state_variables"] = ["X"]
    config_data["process"]["drift"] = {"X": "r * X"}
    config_data["process"]["diffusion"] = {"X": "sigma * X"}
    config_data["numerics"]["grid"]["lower"] = {"X": 0.0}
    config_data["numerics"]["grid"]["upper"] = {"X": 400.0}
    config_data["numerics"]["grid"]["points"] = {"X": 401}
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="supports 1D state variable S only"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_rejects_non_european_exercise() -> None:
    config_data = _valid_config().model_dump()
    config_data["instrument"]["exercise"] = "american"
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="supports European exercise only"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_requires_style() -> None:
    config_data = _valid_config().model_dump()
    config_data["instrument"]["style"] = None
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires instrument.style"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_requires_spot_and_strike() -> None:
    config_data = _valid_config().model_dump()
    del config_data["process"]["parameters"]["S0"]
    del config_data["process"]["parameters"]["K"]
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires S0 \\(or spot\\) and K \\(or strike\\)"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_requires_rate_and_volatility() -> None:
    config_data = _valid_config().model_dump()
    del config_data["process"]["parameters"]["r"]
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires r and sigma"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_rejects_non_flat_risk_free_curve() -> None:
    config_data = _valid_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.0],
            "rates": [0.03, 0.035],
        }
    }
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires a flat market.risk_free_curve"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_rejects_non_flat_dividend_curve() -> None:
    config_data = _valid_config().model_dump()
    config_data["market"] = {
        "dividend_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.0],
            "rates": [0.01, 0.012],
        }
    }
    runner = ValidationRunner()

    with pytest.raises(ValidationError, match="requires a flat market.dividend_curve"):
        runner.run_analytical_black_scholes(PricingConfig.model_validate(config_data))


def test_validation_runner_supports_flat_market_overrides() -> None:
    config_data = _valid_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {"kind": "flat", "rate": 0.04},
        "dividend_curve": {"kind": "flat", "rate": 0.01},
        "volatility": {"kind": "constant", "vol": 0.25},
    }
    runner = ValidationRunner()
    outcome = runner.run_analytical_black_scholes(
        PricingConfig.model_validate(config_data),
        tolerance=0.75,
    )

    assert outcome.passed
