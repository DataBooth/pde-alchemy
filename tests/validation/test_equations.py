"""Tests for constrained LaTeX equation validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy.exceptions import ValidationError
from pdealchemy.validation.equations import validate_equation_library


def test_validate_equation_library_passes_for_supported_subset(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "payoff.md").write_text(
        "\n".join(
            [
                "European call payoff",
                "",
                r"\[",
                r"V(T, S) = \max(S - K, 0)",
                r"\]",
            ]
        ),
        encoding="utf-8",
    )
    (library_dir / "pde.md").write_text(
        "\n".join(
            [
                "Black-Scholes PDE",
                "",
                r"\[",
                r"\frac{\partial V}{\partial t} + r S \frac{\partial V}{\partial S} - rV = 0",
                r"\]",
            ]
        ),
        encoding="utf-8",
    )

    summary = validate_equation_library(library_dir)

    assert summary.files_scanned == 2
    assert summary.equation_blocks_validated == 2


def test_validate_equation_library_rejects_unsupported_command(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "invalid.md").write_text(
        "\n".join(
            [
                "Invalid command",
                "",
                r"\[",
                r"V(T, S) = \foobar(S)",
                r"\]",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="unsupported LaTeX command"):
        _ = validate_equation_library(library_dir)


def test_validate_equation_library_rejects_invalid_algebraic_expression(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "invalid_expr.md").write_text(
        "\n".join(
            [
                "Invalid algebraic expression",
                "",
                r"\[",
                r"V(T, S) = \max(S - , 0)",
                r"\]",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="could not be parsed by the constrained SymPy"):
        _ = validate_equation_library(library_dir)


def test_validate_equation_library_rejects_missing_directory(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_library"

    with pytest.raises(ValidationError, match="directory does not exist"):
        _ = validate_equation_library(missing_path)
