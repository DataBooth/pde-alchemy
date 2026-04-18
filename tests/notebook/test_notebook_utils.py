"""Tests for notebook equation utility helpers."""

from __future__ import annotations

import builtins
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from pdealchemy import notebook_utils
from pdealchemy.exceptions import ConfigError


def _fake_marimo_module() -> SimpleNamespace:
    return SimpleNamespace(md=lambda text: text)


def test_math_eq_renders_raw_latex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.math_eq(r"\sigma(t, S) = \sigma")

    assert rendered == "\\[\n\\sigma(t, S) = \\sigma\n\\]"


def test_spec_md_renders_raw_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.spec_md("Crank-Nicolson discretisation")

    assert rendered == "Crank-Nicolson discretisation"


def test_spec_md_loads_markdown_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markdown_file = tmp_path / "discretisation.md"
    markdown_file.write_text("Scheme: Crank-Nicolson", encoding="utf-8")
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.spec_md(str(markdown_file))

    assert rendered == "Scheme: Crank-Nicolson"


def test_math_eq_renders_named_equation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.math_eq(
        r"\frac{\partial V}{\partial t} - rV = 0",
        name="Main PDE operator",
    )

    assert rendered.startswith("### Main PDE operator")
    assert "\\[\n\\frac{\\partial V}{\\partial t} - rV = 0\n\\]" in rendered


def test_math_eq_extracts_first_latex_block_from_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "equation.md"
    equation_file.write_text(
        "\n".join(
            [
                "Intro text",
                "",
                "\\[",
                "V(T, S) = \\max(S-K, 0)",
                "\\]",
                "",
                "\\[",
                "ignored second block",
                "\\]",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.math_eq(str(equation_file))

    assert rendered == "\\[\nV(T, S) = \\max(S-K, 0)\n\\]"


def test_math_eq_uses_full_file_text_when_no_latex_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "plain_text.md"
    equation_file.write_text("No latex delimiters here.", encoding="utf-8")
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    rendered = notebook_utils.math_eq(str(equation_file))

    assert rendered == "\\[\nNo latex delimiters here.\n\\]"


def test_math_eq_returns_error_message_when_file_read_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "broken.md"
    equation_file.write_text("content", encoding="utf-8")
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", _fake_marimo_module)

    def _raise_read_error(*_args: Any, **_kwargs: Any) -> str:
        raise OSError("Cannot read file")

    monkeypatch.setattr(Path, "read_text", _raise_read_error)

    rendered = notebook_utils.math_eq(str(equation_file))

    assert "**Error loading equation file**" in rendered
    assert "Cannot read file" in rendered


def test_load_marimo_module_raises_config_error_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def _fake_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "marimo":
            raise ModuleNotFoundError("No module named 'marimo'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(ConfigError, match="marimo is required for notebook helpers"):
        _ = notebook_utils._load_marimo_module()
