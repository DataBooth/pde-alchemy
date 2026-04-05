"""Tests for the py-pde pricing adapter."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pde.solvers.base import ConvergenceError

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.adapters import py_pde
from pdealchemy.core.adapters.py_pde import price_with_py_pde
from pdealchemy.exceptions import PricingError


def _base_config() -> PricingConfig:
    return PricingConfig.model_validate(
        {
            "metadata": {"name": "py-pde baseline"},
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
                "backend": "py_pde",
                "scheme": "crank_nicolson",
                "time_steps": 120,
                "damping_steps": 0,
                "grid": {
                    "lower": {"S": 0.0},
                    "upper": {"S": 400.0},
                    "points": {"S": 201},
                },
            },
        }
    )


@dataclass
class _FakeSolvedState:
    value: float

    def interpolate(self, _point: object) -> float:
        return self.value


def test_price_with_py_pde_handles_put_style(monkeypatch: pytest.MonkeyPatch) -> None:
    config_data = _base_config()
    config_data.instrument.style = "put"
    monkeypatch.setattr(
        py_pde.pde.PDE,
        "solve",
        lambda _self, *_args, **_kwargs: _FakeSolvedState(5.25),
    )

    result = price_with_py_pde(config_data)
    assert result.backend == "py_pde"
    assert result.price == pytest.approx(5.25)


def test_price_with_py_pde_accepts_flat_market_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_data = _base_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {"kind": "flat", "rate": 0.04},
        "dividend_curve": {"kind": "flat", "rate": 0.01},
        "volatility": {"kind": "constant", "vol": 0.23},
    }
    parsed = PricingConfig.model_validate(config_data)
    monkeypatch.setattr(
        py_pde.pde.PDE,
        "solve",
        lambda _self, *_args, **_kwargs: _FakeSolvedState(11.0),
    )

    result = price_with_py_pde(parsed)
    assert result.price == pytest.approx(11.0)


def test_price_with_py_pde_rejects_non_flat_market_curve() -> None:
    config_data = _base_config().model_dump()
    config_data["market"] = {
        "risk_free_curve": {
            "kind": "zero_curve",
            "times": [0.25, 1.0],
            "rates": [0.03, 0.035],
        }
    }

    with pytest.raises(PricingError, match="supports flat market curves only"):
        price_with_py_pde(PricingConfig.model_validate(config_data))


def test_price_with_py_pde_rejects_non_constant_market_volatility() -> None:
    config_data = _base_config().model_dump()
    config_data["market"] = {
        "volatility": {
            "kind": "term_curve",
            "times": [0.25, 1.0],
            "vols": [0.2, 0.22],
        }
    }

    with pytest.raises(PricingError, match="supports constant market volatility only"):
        price_with_py_pde(PricingConfig.model_validate(config_data))


def test_price_with_py_pde_rejects_missing_style() -> None:
    config_data = _base_config()
    config_data.instrument.style = None

    with pytest.raises(PricingError, match="requires instrument.style"):
        price_with_py_pde(config_data)


def test_price_with_py_pde_rejects_invalid_spot_vol_and_strike() -> None:
    invalid_spot = _base_config()
    invalid_spot.process.parameters["S0"] = 0.0
    with pytest.raises(PricingError, match="Invalid spot parameter"):
        price_with_py_pde(invalid_spot)

    invalid_vol = _base_config()
    invalid_vol.process.parameters["sigma"] = 0.0
    with pytest.raises(PricingError, match="Invalid volatility parameter"):
        price_with_py_pde(invalid_vol)

    invalid_strike = _base_config()
    invalid_strike.process.parameters["K"] = 0.0
    with pytest.raises(PricingError, match="Invalid strike parameter"):
        price_with_py_pde(invalid_strike)


def test_price_with_py_pde_rejects_non_vanilla_routes() -> None:
    non_european = _base_config()
    non_european.instrument.exercise = "american"
    with pytest.raises(PricingError, match="supports European exercise only"):
        price_with_py_pde(non_european)

    exotic = _base_config().model_dump()
    exotic["instrument"]["kind"] = "exotic_option"
    with pytest.raises(PricingError, match="supports vanilla routes only"):
        price_with_py_pde(PricingConfig.model_validate(exotic))


def test_price_with_py_pde_rejects_bounds_and_spot_domain() -> None:
    invalid_bounds = _base_config()
    invalid_bounds.numerics.grid.upper["S"] = 0.0
    with pytest.raises(PricingError, match="Invalid spatial bounds"):
        price_with_py_pde(invalid_bounds)

    out_of_domain = _base_config()
    out_of_domain.process.parameters["S0"] = 500.0
    out_of_domain.numerics.grid.upper["S"] = 300.0
    with pytest.raises(PricingError, match="outside py_pde log-space grid bounds"):
        price_with_py_pde(out_of_domain)


def test_price_with_py_pde_rejects_invalid_solver_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_data = _base_config()

    monkeypatch.setattr(
        py_pde.pde.PDE,
        "solve",
        lambda _self, *_args, **_kwargs: None,
    )
    with pytest.raises(PricingError, match="did not return a scalar field state"):
        price_with_py_pde(config_data)

    monkeypatch.setattr(
        py_pde.pde.PDE,
        "solve",
        lambda _self, *_args, **_kwargs: _FakeSolvedState(float("nan")),
    )
    with pytest.raises(PricingError, match="produced an invalid option value"):
        price_with_py_pde(config_data)


def test_price_with_py_pde_wraps_convergence_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_data = _base_config()

    def _raise_convergence_error(_self: object, *_args: object, **_kwargs: object) -> object:
        raise ConvergenceError("failed")

    monkeypatch.setattr(py_pde.pde.PDE, "solve", _raise_convergence_error)
    with pytest.raises(PricingError, match="did not converge"):
        price_with_py_pde(config_data)
