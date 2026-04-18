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


def _extract_first_latex_block(text: str) -> str:
    """Extract the first LaTeX display block from markdown-like content."""
    match = re.search(r"\\\[(.+?)\\\]", text, re.DOTALL)
    if match is None:
        return text.strip()
    return match.group(1).strip()


def _read_equation_source(source_path: Path) -> str:
    """Read equation source content from disk."""
    return source_path.read_text(encoding="utf-8")


def math_eq(content: str, *, name: str | None = None) -> object:
    """Render LaTeX content or file-backed LaTeX with an optional equation heading."""
    mo = _load_marimo_module()
    candidate_path = Path(content).expanduser()
    if candidate_path.is_file():
        try:
            source_text = _read_equation_source(candidate_path)
            latex = _extract_first_latex_block(source_text)
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


def math_eq_editor(
    content: str,
    *,
    name: str | None = None,
    save_label: str = "Save equation file",
) -> object:
    """Render an inline markdown equation editor with save and preview controls."""
    mo = _load_marimo_module()
    source_path = Path(content).expanduser()
    if not source_path.is_file():
        return mo.md(
            f"**Error loading equation file** `{content}`: file not found. "
            "Provide a valid markdown equation path."
        )
    try:
        source_text = _read_equation_source(source_path)
    except OSError as exc:
        return mo.md(f"**Error loading equation file** `{content}`: {exc}")
    get_source_text, set_source_text = mo.state(source_text)

    source_editor = mo.ui.code_editor(
        value=source_text,
        language="markdown",
        label=f"Equation source: {content}",
        on_change=set_source_text,
    )

    def _save_source(_value: object) -> str:
        try:
            source_path.write_text(str(get_source_text()), encoding="utf-8")
        except OSError as exc:
            return f"Save failed: {exc}"
        return f"Saved `{content}`."

    save_button = mo.ui.button(
        on_click=_save_source,
        label=save_label,
        kind="success",
    )
    preview = _render_equation_block(
        latex=_extract_first_latex_block(str(get_source_text())),
        name=name,
        mo=mo,
    )
    return mo.vstack(
        [
            mo.md(f"### Inline equation source editor\n\n`{content}`"),
            source_editor,
            save_button,
            mo.md("_Edit the source and click Save equation file to persist changes._"),
            preview,
        ]
    )
