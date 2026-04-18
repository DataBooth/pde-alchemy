"""CLI tests for notebook-to-toml workflow."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pdealchemy.cli.app import app

runner = CliRunner()


def _write_notebook(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_basic_notebook(path: Path) -> None:
    _write_notebook(
        path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq",
            "",
            "app = mo.App()",
            'mo.md("# Demo Spec")',
            "",
            "@app.cell",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq("library/pde/black_scholes.md")',
        ],
    )


def test_notebook_to_toml_command_generates_file(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec.py"
    _write_basic_notebook(notebook_path)
    output_path = tmp_path / "generated.toml"

    result = runner.invoke(
        app,
        [
            "notebook-to-toml",
            str(notebook_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert output_path.exists()
    rendered = output_path.read_text(encoding="utf-8")
    assert "[mathematics.operator]" in rendered


def test_notebook_to_toml_command_supports_default_output_path(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_default_output.py"
    _write_basic_notebook(notebook_path)

    result = runner.invoke(app, ["notebook-to-toml", str(notebook_path)])

    assert result.exit_code == 0, result.stdout
    default_output_path = notebook_path.with_suffix(".toml")
    assert default_output_path.exists()


def test_notebook_to_toml_command_overwrites_existing_file(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_overwrite.py"
    _write_basic_notebook(notebook_path)
    output_path = tmp_path / "generated.toml"
    output_path.write_text("stale-content\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "notebook-to-toml",
            str(notebook_path),
            "--output",
            str(output_path),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0, result.stdout
    rendered = output_path.read_text(encoding="utf-8")
    assert "stale-content" not in rendered
    assert "[mathematics.operator]" in rendered


def test_notebook_to_toml_command_returns_error_for_unmappable_notebook(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_invalid.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "app = mo.App()",
            "",
            "@app.cell",
            "def helper():",
            '    mo.md("No mapped semantic role")',
        ],
    )

    result = runner.invoke(app, ["notebook-to-toml", str(notebook_path)])

    assert result.exit_code == 2
    assert "No mappable specification cells were found" in result.stdout
