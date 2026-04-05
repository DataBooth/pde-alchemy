"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from pdealchemy.cli.app import app

runner = CliRunner()


def _valid_config_toml() -> str:
    return dedent(
        """
        [metadata]
        name = "European call baseline"

        [process]
        state_variables = ["S"]
        parameters = { S0 = 100.0, r = 0.05, sigma = 0.2, K = 100.0 }
        drift = { S = "r * S" }
        diffusion = { S = "sigma * S" }

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

        [numerics.grid]
        lower = { S = 0.0 }
        upper = { S = 400.0 }
        points = { S = 401 }
        """
    ).strip()


def _exotic_config_toml() -> str:
    return dedent(
        """
        [metadata]
        name = "Exotic combo baseline"

        [process]
        state_variables = ["S"]
        parameters = { S0 = 100.0, r = 0.03, sigma = 0.25, K = 100.0 }
        drift = { S = "r * S" }
        diffusion = { S = "sigma * S" }

        [instrument]
        kind = "exotic_option"
        payoff = "max(S - K, 0)"
        maturity = 1.0
        exercise = "european"
        style = "call"

        [features.barrier]
        type = "up_and_out"
        level = 145.0
        rebate = 0.0

        [features.asian]
        averaging = "discrete_arithmetic"
        observation_times = [0.25, 0.5, 0.75, 1.0]

        [[features.dividends.events]]
        time = 0.30
        amount = 0.75

        [[features.dividends.events]]
        time = 0.65
        amount = 0.75

        [numerics]
        backend = "quantlib"
        scheme = "crank_nicolson"
        time_steps = 200
        damping_steps = 0

        [numerics.grid]
        lower = { S = 0.0 }
        upper = { S = 400.0 }
        points = { S = 401 }

        [numerics.monte_carlo]
        paths = 5000
        seed = 42
        antithetic = true
        """
    ).strip()


def test_help_includes_expected_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "price" in result.output
    assert "validate" in result.output
    assert "explain" in result.output


def test_validate_accepts_valid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_valid_config_toml(), encoding="utf-8")

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 0
    assert "Validation successful" in result.output
    assert "backend `quantlib`" in result.output


def test_validate_analytical_passes_for_vanilla(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_valid_config_toml(), encoding="utf-8")

    result = runner.invoke(
        app,
        ["validate", str(config_path), "--analytical", "--tolerance", "0.75"],
    )

    assert result.exit_code == 0
    assert "Analytical benchmark: passed" in result.output


def test_validate_rejects_schema_violation(tmp_path: Path) -> None:
    invalid_config = _valid_config_toml().replace(
        'drift = { S = "r * S" }',
        'drift = { X = "r * X" }',
    )
    config_path = tmp_path / "invalid.toml"
    config_path.write_text(invalid_config, encoding="utf-8")

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 2
    assert "failed schema validation" in result.output
    assert "drift keys must match process.state_variables" in result.output


def test_validate_rejects_unknown_symbol_expression(tmp_path: Path) -> None:
    invalid_config = _valid_config_toml().replace(
        'payoff = "max(S - K, 0)"',
        'payoff = "max(X - K, 0)"',
    )
    config_path = tmp_path / "invalid_symbol.toml"
    config_path.write_text(invalid_config, encoding="utf-8")

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 2
    assert "Failed to parse instrument.payoff" in result.output
    assert "unknown symbols" in result.output


def test_validate_analytical_rejects_exotic_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_exotic_config_toml(), encoding="utf-8")

    result = runner.invoke(app, ["validate", str(config_path), "--analytical"])

    assert result.exit_code == 2
    assert "only available for non-exotic" in result.output
    assert "configs" in result.output


def test_explain_markdown_includes_state_variables(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_valid_config_toml(), encoding="utf-8")

    result = runner.invoke(app, ["explain", str(config_path), "--format", "markdown"])

    assert result.exit_code == 0
    assert "State variables" in result.output
    assert "Drift" in result.output


def test_price_returns_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_valid_config_toml(), encoding="utf-8")

    result = runner.invoke(app, ["price", str(config_path)])

    assert result.exit_code == 0
    assert "Pricing successful" in result.output
    assert "Backend: quantlib" in result.output


def test_price_exotic_combo_returns_value(tmp_path: Path) -> None:
    config_path = tmp_path / "exotic.toml"
    config_path.write_text(_exotic_config_toml(), encoding="utf-8")

    result = runner.invoke(app, ["price", str(config_path)])

    assert result.exit_code == 0
    assert "Pricing successful" in result.output
    assert "MonteCarloDiscreteAsianBarrierDividendEngine" in result.output


def test_validate_rejects_missing_file() -> None:
    result = runner.invoke(app, ["validate", "does-not-exist.toml"])
    assert result.exit_code == 2
    assert "Configuration file not found" in result.output
