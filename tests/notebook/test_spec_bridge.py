"""Tests for bridging notebook specification TOML into runtime TOML."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from pdealchemy.exceptions import ConfigError
from pdealchemy.spec_bridge import spec_to_runtime_toml_content, spec_to_runtime_toml_file


def test_spec_to_runtime_toml_content_renders_runtime_shape(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "spec.toml"
    write_spec_toml(spec_path)

    rendered = spec_to_runtime_toml_content(spec_path)

    assert "[process]" in rendered
    assert 'state_variables = ["S"]' in rendered
    assert "[instrument]" in rendered
    assert 'kind = "vanilla_option"' in rendered
    assert 'payoff = "max(S - K, 0)"' in rendered
    assert "[numerics.grid]" in rendered


def test_spec_to_runtime_toml_file_writes_default_pricing_suffix(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "spec_black_scholes.toml"
    write_spec_toml(spec_path)

    output_path = spec_to_runtime_toml_file(spec_path, overwrite=True)
    assert output_path == tmp_path / "spec_black_scholes.pricing.toml"
    assert output_path.exists()


def test_spec_to_runtime_toml_file_rewrites_blueprint_suffix(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "black_scholes_blueprint.toml"
    write_spec_toml(spec_path)

    output_path = spec_to_runtime_toml_file(spec_path, overwrite=True)

    assert output_path == tmp_path / "black_scholes_pricing.toml"
    assert output_path.exists()


def test_spec_to_runtime_toml_rejects_unsupported_payoff_mapping(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "spec.toml"
    write_spec_toml(spec_path, payoff_file="library/payoff/custom_payoff.md")

    with pytest.raises(ConfigError, match="Unsupported baseline mapping for \\[payoff\\]"):
        _ = spec_to_runtime_toml_content(spec_path)
