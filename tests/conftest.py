"""Shared pytest fixtures for test inputs and builders."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

_DEFAULT_PAYOFF_FILE = "library/payoff/vanilla_call.md"


def _write_spec_toml(path: Path, *, payoff_file: str = _DEFAULT_PAYOFF_FILE) -> None:
    path.write_text(
        "\n".join(
            [
                "[metadata]",
                'name = "Black-Scholes European Call — Specification"',
                "",
                "[instrument]",
                'description = "European vanilla call option in AUD."',
                'markdown = "European Call"',
                "",
                "[mathematics.sde]",
                'equation_file = "library/sde/black_scholes_geometric_brownian_motion.md"',
                "",
                "[mathematics.operator]",
                'equation_file = "library/pde/black_scholes.md"',
                "",
                "[payoff]",
                f'equation_file = "{payoff_file}"',
                "",
                "[numerics]",
                'markdown_file = "library/discretisation/crank_nicolson_standard.md"',
                "",
                "[data.rates]",
                'equation_file = "library/data/rates_flat.md"',
                "",
                "[data.volatility]",
                'equation_file = "library/data/volatility_constant.md"',
            ]
        ),
        encoding="utf-8",
    )


@pytest.fixture
def write_spec_toml() -> Callable[..., None]:
    """Provide a reusable Black-Scholes specification TOML writer."""
    return _write_spec_toml
