"""Tests for explain rendering output."""

from __future__ import annotations

import pytest

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import RenderError
from pdealchemy.math_bridge import build_symbolic_problem
from pdealchemy.render import render_explain_output


def _valid_config() -> PricingConfig:
    return PricingConfig.model_validate(
        {
            "metadata": {"name": "Renderer baseline"},
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
    )


def test_render_text_contains_pde_and_sde_sections() -> None:
    config_data = _valid_config()
    symbolic_problem = build_symbolic_problem(config_data)

    rendered = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="text",
    )

    assert "Stochastic model (SDE)" in rendered
    assert "Pricing PDE" in rendered
    assert "dS" in rendered


def test_render_markdown_contains_expected_headings() -> None:
    config_data = _valid_config()
    symbolic_problem = build_symbolic_problem(config_data)

    rendered = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="markdown",
    )

    assert "# PDEAlchemy Explain" in rendered
    assert "## Stochastic model (SDE)" in rendered
    assert "## Terminal condition" in rendered


def test_render_latex_contains_pde_expression() -> None:
    config_data = _valid_config()
    symbolic_problem = build_symbolic_problem(config_data)

    rendered = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="latex",
    )

    assert "\\frac{\\partial V}{\\partial t}" in rendered
    assert "\\subsection*{Pricing PDE}" in rendered


def test_render_rejects_unsupported_format() -> None:
    config_data = _valid_config()
    symbolic_problem = build_symbolic_problem(config_data)

    with pytest.raises(RenderError, match="Unsupported explain output format"):
        render_explain_output(
            config_data,
            symbolic_problem,
            output_format="html",
        )


def test_render_markdown_includes_exotic_feature_section() -> None:
    config_dict = _valid_config().model_dump()
    config_dict["features"] = {
        "barrier": {"type": "up_and_out", "level": 145.0, "rebate": 0.0},
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
    config_data = PricingConfig.model_validate(config_dict)
    symbolic_problem = build_symbolic_problem(config_data)

    rendered = render_explain_output(
        config_data,
        symbolic_problem,
        output_format="markdown",
    )

    assert "## Discrete / exotic features" in rendered
    assert "Barrier up_and_out" in rendered
    assert "Discrete dividends" in rendered
