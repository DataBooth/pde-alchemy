"""Notebook-to-TOML conversion for mathematics-first specification notebooks."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pdealchemy.exceptions import ConfigError

_CELL_SECTION_MAP: dict[str, tuple[str, ...]] = {
    "instrument": ("instrument",),
    "numeraire": ("numeraire",),
    "pde": ("mathematics", "operator"),
    "payoff": ("payoff",),
    "boundary_lower": ("boundary", "lower"),
    "boundary_upper": ("boundary", "upper"),
    "discretisation": ("numerics",),
}
_SUPPORTED_EQUATION_HELPERS = {"math_eq", "eq_from_file"}
_SUPPORTED_MARKDOWN_HELPERS = {"mo.md"}


@dataclass(frozen=True)
class NotebookCell:
    """Extracted details from a notebook cell function."""

    function_name: str
    description: str | None
    markdown: str | None
    equation_content: str | None


def _extract_string_argument(call: ast.Call) -> str | None:
    """Return the first positional string argument from a call expression."""
    if not call.args:
        return None
    first_argument = call.args[0]
    if isinstance(first_argument, ast.Constant) and isinstance(first_argument.value, str):
        return first_argument.value.strip()
    return None


def _call_name(node: ast.Call) -> str | None:
    """Build a dotted helper name from a call target."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    return None


def _extract_cell_details(function_node: ast.FunctionDef) -> NotebookCell:
    """Extract markdown and equation calls from a notebook cell function."""
    markdown_content: str | None = None
    equation_content: str | None = None
    for statement in function_node.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        helper_name = _call_name(call)
        if helper_name in _SUPPORTED_MARKDOWN_HELPERS and markdown_content is None:
            markdown_content = _extract_string_argument(call)
        if helper_name in _SUPPORTED_EQUATION_HELPERS and equation_content is None:
            equation_content = _extract_string_argument(call)
    return NotebookCell(
        function_name=function_node.name,
        description=ast.get_docstring(function_node),
        markdown=markdown_content,
        equation_content=equation_content,
    )


def _is_app_cell(function_node: ast.FunctionDef) -> bool:
    """Return true when a function is decorated as a marimo app cell."""
    for decorator in function_node.decorator_list:
        if (
            isinstance(decorator, ast.Attribute)
            and decorator.attr == "cell"
            and isinstance(decorator.value, ast.Name)
            and decorator.value.id == "app"
        ):
            return True
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "cell"
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "app"
        ):
            return True
    return False


def _table_path_for_cell(cell_name: str) -> tuple[str, ...] | None:
    """Resolve target table path for a notebook cell function name."""
    if cell_name in _CELL_SECTION_MAP:
        return _CELL_SECTION_MAP[cell_name]
    if cell_name.startswith("data_") and len(cell_name) > len("data_"):
        return ("data", cell_name.split("data_", maxsplit=1)[1])
    return None


def _looks_like_path(value: str) -> bool:
    """Heuristically classify an equation token as a file path."""
    if value.endswith(".md"):
        return True
    if "/" in value or "\\" in value:
        return True
    return value.startswith(".")


def _render_toml_string(value: str) -> str:
    """Render a TOML string with support for multiline content."""
    if "\n" in value:
        escaped = value.replace("'''", "\\'\\'\\'")
        return f"'''\n{escaped}\n'''"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_section(table_path: Iterable[str], values: dict[str, str]) -> list[str]:
    """Render one TOML table section."""
    lines = [f"[{'.'.join(table_path)}]"]
    for key, value in values.items():
        lines.append(f"{key} = {_render_toml_string(value)}")
    lines.append("")
    return lines


def _extract_notebook_title(module: ast.Module) -> str | None:
    """Extract the first top-level markdown heading if present."""

    def _heading_from_call(call: ast.Call) -> str | None:
        helper_name = _call_name(call)
        if helper_name not in _SUPPORTED_MARKDOWN_HELPERS:
            return None
        maybe_markdown = _extract_string_argument(call)
        if maybe_markdown is None:
            return None
        for line in maybe_markdown.splitlines():
            heading = line.strip()
            if heading.startswith("#"):
                return heading.lstrip("#").strip()
        return None

    for statement in module.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        maybe_heading = _heading_from_call(statement.value)
        if maybe_heading is not None:
            return maybe_heading

    for statement in module.body:
        if not isinstance(statement, ast.FunctionDef) or not _is_app_cell(statement):
            continue
        for cell_statement in statement.body:
            if isinstance(cell_statement, ast.Expr) and isinstance(cell_statement.value, ast.Call):
                maybe_heading = _heading_from_call(cell_statement.value)
                if maybe_heading is not None:
                    return maybe_heading
    return None


def notebook_to_toml_content(notebook_path: Path) -> str:
    """Convert a specification notebook into TOML text."""
    if not notebook_path.exists():
        raise ConfigError(
            f"Notebook file not found: {notebook_path}",
            suggestion="Check the notebook path and try again.",
        )
    if not notebook_path.is_file():
        raise ConfigError(
            f"Notebook path is not a file: {notebook_path}",
            suggestion="Provide a path to a marimo notebook file.",
        )

    notebook_text = notebook_path.read_text(encoding="utf-8")
    try:
        module = ast.parse(notebook_text, filename=str(notebook_path))
    except SyntaxError as exc:
        raise ConfigError(
            "Notebook file could not be parsed as Python.",
            details=str(exc),
            suggestion="Fix syntax errors and re-run notebook-to-toml.",
        ) from exc

    extracted_cells: list[NotebookCell] = [
        _extract_cell_details(node)
        for node in module.body
        if isinstance(node, ast.FunctionDef) and _is_app_cell(node)
    ]
    if not extracted_cells:
        raise ConfigError(
            "No marimo app cells were found in the notebook.",
            suggestion="Ensure notebook cells are declared with @app.cell decorators.",
        )

    lines: list[str] = []
    lines.append(f"# Generated from {notebook_path.name} by pdealchemy notebook-to-toml")
    lines.append("")

    title = _extract_notebook_title(module)
    if title is not None:
        metadata_values = {
            "name": title,
            "source_notebook": str(notebook_path),
        }
        lines.extend(_render_section(("metadata",), metadata_values))

    populated_sections = 0
    for cell in extracted_cells:
        table_path = _table_path_for_cell(cell.function_name)
        if table_path is None:
            continue
        values: dict[str, str] = {}
        if cell.description:
            values["description"] = cell.description.strip()
        if cell.markdown:
            values["markdown"] = cell.markdown.strip()
        if cell.equation_content:
            if _looks_like_path(cell.equation_content):
                values["equation_file"] = cell.equation_content.strip()
            else:
                values["equation"] = cell.equation_content.strip()
        if not values:
            continue
        lines.extend(_render_section(table_path, values))
        populated_sections += 1

    if populated_sections == 0:
        raise ConfigError(
            "No mappable specification cells were found.",
            details=(
                "Expected at least one of: instrument, numeraire, pde, payoff, "
                "boundary_lower, boundary_upper, discretisation, or data_*."
            ),
            suggestion="Rename notebook cells to the expected semantic function names.",
        )

    return "\n".join(lines).rstrip() + "\n"


def notebook_to_toml_file(
    notebook_path: Path,
    *,
    output_path: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Write TOML converted from a notebook and return the output path."""
    rendered = notebook_to_toml_content(notebook_path)
    target_path = output_path if output_path is not None else notebook_path.with_suffix(".toml")
    if target_path.exists() and not overwrite:
        raise ConfigError(
            f"Output file already exists: {target_path}",
            suggestion="Use --overwrite to replace it or provide --output <path>.",
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(rendered, encoding="utf-8")
    return target_path
