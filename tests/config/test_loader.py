"""Tests for configuration loading helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy.config import loader
from pdealchemy.config.loader import (
    _format_validation_errors,
    _load_toml_file,
    load_pricing_config,
    load_symbolic_problem,
)
from pdealchemy.exceptions import ConfigError


def _valid_toml() -> str:
    return """
[metadata]
name = "Loader baseline"

[process]
state_variables = ["S"]

[process.parameters]
S0 = 100.0
r = 0.05
sigma = 0.2
K = 100.0

[process.drift]
S = "r * S"

[process.diffusion]
S = "sigma * S"

[instrument]
kind = "vanilla_option"
payoff = "max(S - K, 0)"
maturity = 1.0
exercise = "european"
style = "call"

[numerics]
backend = "quantlib"
scheme = "crank_nicolson"
time_steps = 200
damping_steps = 0

[numerics.grid.lower]
S = 0.0

[numerics.grid.upper]
S = 400.0

[numerics.grid.points]
S = 401
"""


def test_load_pricing_config_success(tmp_path: Path) -> None:
    config_path = tmp_path / "valid.toml"
    config_path.write_text(_valid_toml(), encoding="utf-8")

    config_data = load_pricing_config(config_path)
    assert tuple(config_data.process.state_variables) == ("S",)
    assert config_data.numerics.backend == "quantlib"


def test_load_symbolic_problem_success(tmp_path: Path) -> None:
    config_path = tmp_path / "valid.toml"
    config_path.write_text(_valid_toml(), encoding="utf-8")

    symbolic_problem = load_symbolic_problem(config_path)
    assert symbolic_problem.state_variables == ("S",)
    assert "S" in symbolic_problem.drift
    assert "S" in symbolic_problem.diffusion


def test_load_pricing_config_rejects_missing_file(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="file not found"):
        load_pricing_config(config_path)


def test_load_pricing_config_rejects_non_file_path(tmp_path: Path) -> None:
    config_path = tmp_path / "configs"
    config_path.mkdir()

    with pytest.raises(ConfigError, match="path is not a file"):
        load_pricing_config(config_path)


def test_load_pricing_config_rejects_invalid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.toml"
    config_path.write_text("not = [valid", encoding="utf-8")

    with pytest.raises(ConfigError, match="not valid TOML"):
        load_pricing_config(config_path)


def test_load_pricing_config_rejects_schema_errors(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid_schema.toml"
    config_path.write_text("[metadata]\nname = \"Invalid\"\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="failed schema validation") as exc_info:
        load_pricing_config(config_path)

    assert exc_info.value.details is not None
    assert "Field required" in exc_info.value.details


def test_load_toml_rejects_non_table_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "root.toml"
    config_path.write_text("x = 1\n", encoding="utf-8")

    monkeypatch.setattr(loader.tomllib, "load", lambda _file_obj: ["not", "a", "table"])
    with pytest.raises(ConfigError, match="root must be a TOML table"):
        _load_toml_file(config_path)


def test_format_validation_errors_truncates_to_max_issues() -> None:
    class DummyValidationError:
        def errors(self) -> list[dict[str, object]]:
            return [
                {"loc": ("root", index), "msg": "bad value"}
                for index in range(10)
            ]

    formatted = _format_validation_errors(DummyValidationError())  # type: ignore[arg-type]
    assert "- root.0: bad value" in formatted
    assert "- ... and 2 more issue(s)." in formatted
