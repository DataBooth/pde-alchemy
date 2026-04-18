"""CLI tests for specification-to-runtime TOML bridge workflow."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from pdealchemy.cli.app import app

runner = CliRunner()


def test_spec_to_runtime_toml_command_generates_runtime_file(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "spec.toml"
    write_spec_toml(spec_path)
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


def test_spec_to_runtime_toml_command_rejects_unsupported_baseline(
    tmp_path: Path,
    write_spec_toml: Callable[..., None],
) -> None:
    spec_path = tmp_path / "spec.toml"
    write_spec_toml(spec_path, payoff_file="library/payoff/custom_payoff.md")

    result = runner.invoke(app, ["spec-to-runtime-toml", str(spec_path)])

    assert result.exit_code == 2
    assert "Unsupported baseline mapping" in result.stdout
