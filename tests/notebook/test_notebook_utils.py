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


class _FakeCodeEditor:
    def __init__(self, value: str) -> None:
        self.value = value


class _FakeButton:
    def __init__(self, on_click: Any) -> None:
        self._on_click = on_click
        self.value: Any = None

    def click(self) -> None:
        self.value = self._on_click(None)


class _NoValueReadButton:
    def __init__(self, on_click: Any) -> None:
        self._on_click = on_click

    @property
    def value(self) -> Any:
        raise RuntimeError("Accessing button.value in creating cell is not allowed")

    def click(self) -> Any:
        return self._on_click(None)


class _FakeUi:
    def code_editor(
        self,
        value: str,
        *,
        language: str,
        label: str,
    ) -> _FakeCodeEditor:
        _ = (language, label)
        return _FakeCodeEditor(value)

    def button(
        self,
        *,
        on_click: Any,
        label: str,
        kind: str,
    ) -> _FakeButton:
        _ = (label, kind)
        return _FakeButton(on_click)


class _FakeEditorMarimo:
    ui = _FakeUi()

    @staticmethod
    def md(text: str) -> tuple[str, str]:
        return ("md", text)

    @staticmethod
    def vstack(blocks: list[object]) -> tuple[str, list[object]]:
        return ("vstack", blocks)


class _NoValueReadUi(_FakeUi):
    def button(
        self,
        *,
        on_click: Any,
        label: str,
        kind: str,
    ) -> _NoValueReadButton:
        _ = (label, kind)
        return _NoValueReadButton(on_click)


class _NoValueReadMarimo:
    ui = _NoValueReadUi()

    @staticmethod
    def md(text: str) -> tuple[str, str]:
        return ("md", text)

    @staticmethod
    def vstack(blocks: list[object]) -> tuple[str, list[object]]:
        return ("vstack", blocks)


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


def test_math_eq_editor_renders_inline_editor_with_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "equation.md"
    equation_file.write_text(
        "\n".join(
            [
                "PDE notes",
                "\\[",
                "\\frac{\\partial V}{\\partial t} + rSV_S = 0",
                "\\]",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", lambda: _FakeEditorMarimo)

    rendered = notebook_utils.math_eq_editor(str(equation_file), name="Main PDE operator")

    assert rendered[0] == "vstack"
    editor = next(block for block in rendered[1] if isinstance(block, _FakeCodeEditor))
    preview = rendered[1][-1]
    assert "PDE notes" in editor.value
    assert preview[0] == "md"
    assert "### Main PDE operator" in preview[1]
    assert "\\frac{\\partial V}{\\partial t} + rSV_S = 0" in preview[1]


def test_math_eq_editor_persists_edited_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "equation.md"
    equation_file.write_text("\\[\nS\n\\]", encoding="utf-8")
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", lambda: _FakeEditorMarimo)

    rendered = notebook_utils.math_eq_editor(str(equation_file))
    editor = next(block for block in rendered[1] if isinstance(block, _FakeCodeEditor))
    button = next(block for block in rendered[1] if isinstance(block, _FakeButton))
    editor.value = "\\[\nS-K\n\\]"

    button.click()

    assert equation_file.read_text(encoding="utf-8") == "\\[\nS-K\n\\]"
    assert button.value == f"Saved `{equation_file}`."


def test_math_eq_editor_rejects_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", lambda: _FakeEditorMarimo)

    rendered = notebook_utils.math_eq_editor("library/pde/missing.md")

    assert rendered[0] == "md"
    assert "Error loading equation file" in rendered[1]
    assert "file not found" in rendered[1]


def test_math_eq_editor_does_not_access_button_value_in_creator_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equation_file = tmp_path / "equation.md"
    equation_file.write_text("\\[\nS\n\\]", encoding="utf-8")
    monkeypatch.setattr(notebook_utils, "_load_marimo_module", lambda: _NoValueReadMarimo)

    rendered = notebook_utils.math_eq_editor(str(equation_file))

    assert rendered[0] == "vstack"


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
