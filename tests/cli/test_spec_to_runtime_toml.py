"""CLI tests for specification-to-runtime TOML bridge workflow."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pdealchemy.cli.app import app

runner = CliRunner()


def _write_spec_toml(path: Path, *, payoff_file: str = "library/payoff/vanilla_call.md") -> None:
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


def test_spec_to_runtime_toml_command_generates_runtime_file(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.toml"
    _write_spec_toml(spec_path)
    runtime_path = tmp_path / "runtime.toml"

    result = runner.invoke(
        app,
        [
            "spec-to-runtime-toml",
            str(spec_path),
            "--output",
            str(runtime_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert runtime_path.exists()
    rendered = runtime_path.read_text(encoding="utf-8")
    assert "[process]" in rendered
    assert "[instrument]" in rendered
    assert "[numerics]" in rendered


def test_spec_to_runtime_toml_command_rejects_unsupported_baseline(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.toml"
    _write_spec_toml(spec_path, payoff_file="library/payoff/custom_payoff.md")

    result = runner.invoke(app, ["spec-to-runtime-toml", str(spec_path)])

    assert result.exit_code == 2
    assert "Unsupported baseline mapping" in result.stdout
