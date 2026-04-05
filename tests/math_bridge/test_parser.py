"""Tests for symbolic parsing and compilation helpers."""

from __future__ import annotations

import pytest

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import MathBridgeError
from pdealchemy.math_bridge import build_symbolic_problem, compile_expression, parse_expression


def _valid_config() -> dict[str, object]:
    return {
        "metadata": {"name": "Math bridge baseline"},
        "process": {
            "state_variables": ["S"],
            "parameters": {"r": 0.05, "sigma": 0.2, "K": 100.0},
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


def test_parse_expression_tracks_symbols() -> None:
    parsed = parse_expression("r * S + K", allowed_symbols={"r", "S", "K"})
    assert set(parsed.symbols) == {"r", "S", "K"}


def test_parse_expression_rejects_unknown_symbols() -> None:
    with pytest.raises(MathBridgeError, match="unknown symbols"):
        parse_expression("r * X", allowed_symbols={"r", "S"})
def test_parse_expression_rejects_unsupported_functions() -> None:
    with pytest.raises(MathBridgeError, match="unsupported function"):
        parse_expression("sin(S)", allowed_symbols={"S"})


def test_compile_expression_with_substitutions() -> None:
    parsed = parse_expression("r * S + K", allowed_symbols={"r", "S", "K"})
    compiled = compile_expression(parsed, substitutions={"r": 0.05, "K": 1.0})

    assert compiled.symbol_order == ("S",)
    assert compiled(100.0) == pytest.approx(6.0)


def test_build_symbolic_problem_from_config() -> None:
    config_data = PricingConfig.model_validate(_valid_config())
    symbolic_problem = build_symbolic_problem(config_data)

    assert symbolic_problem.state_variables == ("S",)
    compiled_drift = compile_expression(
        symbolic_problem.drift["S"],
        substitutions=symbolic_problem.parameter_values,
    )
    assert compiled_drift(100.0) == pytest.approx(5.0)
