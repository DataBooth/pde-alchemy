"""Constrained LaTeX equation validation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from pdealchemy.exceptions import ValidationError

_EQUATION_BLOCK_PATTERN = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
_LATEX_COMMAND_PATTERN = re.compile(r"\\([A-Za-z]+)")
_FRAC_PATTERN = re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
_IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_FUNCTION_CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]+)\)")

_SUPPORTED_LATEX_COMMANDS = {
    "frac",
    "partial",
    "max",
    "min",
    "sqrt",
    "log",
    "exp",
    "sim",
    "int",
    "left",
    "right",
    "sigma",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "theta",
    "rho",
    "mu",
    "lambda",
    "pi",
    "to",
    "infty",
}
_SYMPY_FUNCTION_NAMES = {"max", "min", "sqrt", "log", "exp"}
_SYMPY_FUNCTION_LOCALS: dict[str, object] = {
    "max": sp.Max,
    "min": sp.Min,
    "sqrt": sp.sqrt,
    "log": sp.log,
    "exp": sp.exp,
}
_GREEK_REPLACEMENTS = {
    r"\sigma": "sigma",
    r"\alpha": "alpha",
    r"\beta": "beta",
    r"\gamma": "gamma",
    r"\delta": "delta",
    r"\theta": "theta",
    r"\rho": "rho",
    r"\mu": "mu",
    r"\lambda": "lambda",
    r"\pi": "pi",
}


@dataclass(frozen=True)
class EquationLibraryValidationSummary:
    """Summary of equation library validation results."""

    files_scanned: int
    equation_blocks_validated: int


def _extract_equation_blocks(markdown_text: str) -> list[str]:
    r"""Extract display-math equation blocks delimited by \[ ... \]."""
    return [match.group(1).strip() for match in _EQUATION_BLOCK_PATTERN.finditer(markdown_text)]


def _validate_supported_latex_commands(equation: str, *, markdown_file: Path) -> None:
    """Reject unsupported LaTeX commands in equation text."""
    used_commands = {match.group(1) for match in _LATEX_COMMAND_PATTERN.finditer(equation)}
    unsupported = sorted(
        command for command in used_commands if command not in _SUPPORTED_LATEX_COMMANDS
    )
    if unsupported:
        raise ValidationError(
            "Equation uses unsupported LaTeX command(s).",
            details=f"{markdown_file}: {', '.join(unsupported)}",
            suggestion=(
                "Use the constrained equation subset or extend the validator command allow-list."
            ),
        )


def _contains_non_algebraic_constructs(equation: str) -> bool:
    """Return true when equation uses constructs outside algebraic SymPy conversion."""
    return any(token in equation for token in (r"\partial", r"\int", r"\sim"))


def _replace_frac_blocks(expression: str) -> str:
    r"""Replace simple \frac{a}{b} fragments with (a)/(b)."""
    updated = expression
    while True:
        replaced = _FRAC_PATTERN.sub(r"((\1)/(\2))", updated)
        if replaced == updated:
            return updated
        updated = replaced


def _normalise_latex_to_sympy_subset(equation: str) -> str:
    """Normalise a constrained LaTeX subset into a SymPy-friendly expression string."""
    normalised = equation
    normalised = normalised.replace(r"\left", "").replace(r"\right", "")
    normalised = _replace_frac_blocks(normalised)
    for latex_token, replacement in _GREEK_REPLACEMENTS.items():
        normalised = normalised.replace(latex_token, replacement)
    normalised = (
        normalised.replace(r"\max", "max")
        .replace(r"\min", "min")
        .replace(r"\sqrt", "sqrt")
        .replace(r"\log", "log")
        .replace(r"\exp", "exp")
    )
    normalised = normalised.replace("{", "(").replace("}", ")")
    while True:
        updated = _FUNCTION_CALL_PATTERN.sub(
            lambda match: (
                match.group(0) if match.group(1) in _SYMPY_FUNCTION_NAMES else match.group(1)
            ),
            normalised,
        )
        if updated == normalised:
            break
        normalised = updated
    normalised = normalised.replace("^", "**")
    normalised = re.sub(r"(?<=[0-9A-Za-z_\)])\s+(?=[A-Za-z_(])", " * ", normalised)
    if "=" in normalised:
        left, right = normalised.split("=", maxsplit=1)
        normalised = f"({left}) - ({right})"
    return normalised


def _validate_algebraic_subset_with_sympy(
    equation: str,
    *,
    markdown_file: Path,
) -> None:
    """Validate algebraic equation syntax by normalising then parsing with SymPy."""
    normalised = _normalise_latex_to_sympy_subset(equation)
    candidate_symbols = {
        token
        for token in _IDENTIFIER_PATTERN.findall(normalised)
        if token not in _SYMPY_FUNCTION_NAMES
    }
    symbol_locals = {name: sp.Symbol(name) for name in candidate_symbols}
    locals_dict: dict[str, object] = {**symbol_locals, **_SYMPY_FUNCTION_LOCALS}
    try:
        _ = sp.sympify(  # ty: ignore[no-matching-overload]
            normalised,
            locals=locals_dict,
            evaluate=False,
        )
    except (sp.SympifyError, TypeError) as exc:
        raise ValidationError(
            "Equation could not be parsed by the constrained SymPy validator.",
            details=f"{markdown_file}: {exc}",
            suggestion=(
                "Use supported algebraic LaTeX patterns or move advanced forms to the "
                "non-algebraic constrained subset."
            ),
        ) from exc


def validate_equation_library(library_root: Path) -> EquationLibraryValidationSummary:
    """Validate Markdown equations under a library root using constrained LaTeX rules."""
    if not library_root.exists():
        raise ValidationError(
            "Equation library directory does not exist.",
            details=str(library_root),
            suggestion="Provide an existing directory path for --equation-library.",
        )
    if not library_root.is_dir():
        raise ValidationError(
            "Equation library path is not a directory.",
            details=str(library_root),
            suggestion="Provide a directory containing Markdown equation files.",
        )

    markdown_files = sorted(library_root.rglob("*.md"))
    validated_blocks = 0
    for markdown_file in markdown_files:
        markdown_text = markdown_file.read_text(encoding="utf-8")
        equation_blocks = _extract_equation_blocks(markdown_text)
        for equation in equation_blocks:
            _validate_supported_latex_commands(equation, markdown_file=markdown_file)
            if not _contains_non_algebraic_constructs(equation):
                _validate_algebraic_subset_with_sympy(equation, markdown_file=markdown_file)
            validated_blocks += 1

    return EquationLibraryValidationSummary(
        files_scanned=len(markdown_files),
        equation_blocks_validated=validated_blocks,
    )
