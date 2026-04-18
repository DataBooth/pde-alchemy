"""Helpers for mathematics-first marimo specification notebooks."""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from pdealchemy.exceptions import ConfigError


def _load_marimo_module() -> ModuleType:
    """Import marimo lazily to keep interactive dependencies optional."""
    try:
        import marimo as mo  # pyright: ignore[reportMissingImports]
    except ModuleNotFoundError as exc:
        raise ConfigError(
            "marimo is required for notebook helpers.",
            suggestion=(
                "Install optional interactive dependencies with `uv sync --all-extras --dev`."
            ),
        ) from exc
    return mo


def _render_equation_block(*, latex: str, name: str | None, mo: ModuleType) -> object:
    """Render an equation block with an optional heading."""
    equation_block = f"\\[\n{latex}\n\\]"
    if name is None or not name.strip():
        return mo.md(equation_block)
    return mo.md(f"### {name.strip()}\n\n{equation_block}")


def _render_markdown_block(*, markdown: str, name: str | None, mo: ModuleType) -> object:
    """Render a markdown block with an optional heading."""
    if name is None or not name.strip():
        return mo.md(markdown)
    return mo.md(f"### {name.strip()}\n\n{markdown}")


def math_eq(content: str, *, name: str | None = None) -> object:
    """Render LaTeX content or file-backed LaTeX with an optional equation heading."""
    mo = _load_marimo_module()
    candidate_path = Path(content).expanduser()
    if candidate_path.is_file():
        try:
            text = candidate_path.read_text(encoding="utf-8").strip()
            match = re.search(r"\\\[(.+?)\\\]", text, re.DOTALL)
            latex = match.group(1).strip() if match else text
            return _render_equation_block(latex=latex, name=name, mo=mo)
        except OSError as exc:
            return mo.md(f"**Error loading equation file** `{content}`: {exc}")
    return _render_equation_block(latex=content, name=name, mo=mo)


def spec_md(content: str, *, name: str | None = None) -> object:
    """Render markdown content or file-backed markdown with an optional heading."""
    mo = _load_marimo_module()
    candidate_path = Path(content).expanduser()
    if candidate_path.is_file():
        try:
            markdown_text = candidate_path.read_text(encoding="utf-8").strip()
            return _render_markdown_block(markdown=markdown_text, name=name, mo=mo)
        except OSError as exc:
            return mo.md(f"**Error loading markdown file** `{content}`: {exc}")
    return _render_markdown_block(markdown=content, name=name, mo=mo)
