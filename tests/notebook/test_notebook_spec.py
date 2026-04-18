"""Tests for notebook specification extraction and TOML conversion."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy.exceptions import ConfigError
from pdealchemy.notebook_spec import notebook_to_toml_content, notebook_to_toml_file


def _write_notebook(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_sample_notebook(path: Path) -> None:
    _write_notebook(
        path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq, spec_md",
            "",
            "app = mo.App()",
            "",
            'mo.md("# Black-Scholes European Call — Specification")',
            "",
            "@app.cell",
            "def sde():",
            '    """Risk-neutral asset dynamics."""',
            '    math_eq("library/sde/black_scholes_geometric_brownian_motion.md")',
            "",
            "@app.cell",
            "def instrument():",
            '    """European vanilla call option in AUD."""',
            '    mo.md("European Call")',
            "",
            "@app.cell",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq("library/pde/black_scholes.md")',
            "",
            "@app.cell",
            "def discretisation():",
            '    """Numerical discretisation settings."""',
            '    spec_md("library/discretisation/crank_nicolson_standard.md")',
            "",
            "@app.cell",
            "def data_rates():",
            '    """Risk-free rate source."""',
            '    math_eq("r(t) = 0.05")',
        ],
    )


def test_notebook_to_toml_content_maps_core_cells(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_black_scholes.py"
    _write_sample_notebook(notebook_path)

    rendered = notebook_to_toml_content(notebook_path)

    assert "[metadata]" in rendered
    assert 'name = "Black-Scholes European Call — Specification"' in rendered
    assert "[instrument]" in rendered
    assert 'description = "European vanilla call option in AUD."' in rendered
    assert 'markdown = "European Call"' in rendered
    assert "[mathematics.sde]" in rendered
    assert 'equation_file = "library/sde/black_scholes_geometric_brownian_motion.md"' in rendered
    assert "[mathematics.operator]" in rendered
    assert 'equation_file = "library/pde/black_scholes.md"' in rendered
    assert "[numerics]" in rendered
    assert 'markdown_file = "library/discretisation/crank_nicolson_standard.md"' in rendered
    assert "[data.rates]" in rendered
    assert 'equation = "r(t) = 0.05"' in rendered


def test_notebook_to_toml_supports_app_cell_call_decorator(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_cell_call.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq",
            "",
            "app = mo.App()",
            "",
            'mo.md("# Cell Call Style")',
            "",
            "@app.cell()",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq("library/pde/black_scholes.md")',
        ],
    )

    rendered = notebook_to_toml_content(notebook_path)

    assert "[mathematics.operator]" in rendered
    assert 'description = "Main PDE operator."' in rendered
    assert 'equation_file = "library/pde/black_scholes.md"' in rendered


def test_notebook_to_toml_supports_math_eq_editor_helper(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_math_eq_editor.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq_editor",
            "",
            "app = mo.App()",
            "",
            'mo.md("# Editor Helper")',
            "",
            "@app.cell",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq_editor("library/pde/black_scholes.md", name="Main PDE operator")',
        ],
    )

    rendered = notebook_to_toml_content(notebook_path)

    assert "[mathematics.operator]" in rendered
    assert 'equation_file = "library/pde/black_scholes.md"' in rendered


def test_notebook_to_toml_ignores_unknown_cells(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_mixed_cells.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "app = mo.App()",
            "",
            'mo.md("# Mixed Cell Names")',
            "",
            "@app.cell",
            "def instrument():",
            '    """Known section."""',
            '    mo.md("Instrument")',
            "",
            "@app.cell",
            "def random_notes():",
            '    """Should be ignored."""',
            '    mo.md("Ignore this section")',
        ],
    )

    rendered = notebook_to_toml_content(notebook_path)

    assert "[instrument]" in rendered
    assert "[random_notes]" not in rendered


def test_notebook_to_toml_omits_metadata_without_heading(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_no_heading.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq",
            "",
            "app = mo.App()",
            "",
            'mo.md("Specification intro without heading marker")',
            "",
            "@app.cell",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq("library/pde/black_scholes.md")',
        ],
    )

    rendered = notebook_to_toml_content(notebook_path)

    assert "[metadata]" not in rendered
    assert "[mathematics.operator]" in rendered


def test_notebook_to_toml_extracts_title_from_app_cell(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_title_in_cell.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "from pdealchemy.notebook_utils import math_eq",
            "",
            "app = mo.App()",
            "",
            "@app.cell",
            "def title():",
            '    mo.md("# Title From Cell")',
            "",
            "@app.cell",
            "def pde():",
            '    """Main PDE operator."""',
            '    math_eq("library/pde/black_scholes.md")',
        ],
    )

    rendered = notebook_to_toml_content(notebook_path)

    assert "[metadata]" in rendered
    assert 'name = "Title From Cell"' in rendered


def test_notebook_to_toml_is_deterministic(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_black_scholes.py"
    _write_sample_notebook(notebook_path)

    first_render = notebook_to_toml_content(notebook_path)
    second_render = notebook_to_toml_content(notebook_path)

    assert first_render == second_render


def test_notebook_to_toml_file_writes_output(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_black_scholes.py"
    _write_sample_notebook(notebook_path)
    output_path = tmp_path / "generated_spec.toml"

    written_path = notebook_to_toml_file(notebook_path, output_path=output_path)

    assert written_path == output_path
    assert output_path.exists()
    assert "[instrument]" in output_path.read_text(encoding="utf-8")


def test_notebook_to_toml_file_rejects_overwrite_without_flag(tmp_path: Path) -> None:
    notebook_path = tmp_path / "spec_black_scholes.py"
    _write_sample_notebook(notebook_path)
    output_path = tmp_path / "generated_spec.toml"
    output_path.write_text("already here\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        _ = notebook_to_toml_file(notebook_path, output_path=output_path, overwrite=False)


def test_notebook_to_toml_rejects_missing_file(tmp_path: Path) -> None:
    notebook_path = tmp_path / "missing_notebook.py"

    with pytest.raises(ConfigError, match="Notebook file not found"):
        _ = notebook_to_toml_content(notebook_path)


def test_notebook_to_toml_rejects_directory_path(tmp_path: Path) -> None:
    notebook_directory = tmp_path / "notebook_directory"
    notebook_directory.mkdir()

    with pytest.raises(ConfigError, match="Notebook path is not a file"):
        _ = notebook_to_toml_content(notebook_directory)


def test_notebook_to_toml_rejects_python_syntax_errors(tmp_path: Path) -> None:
    notebook_path = tmp_path / "invalid_syntax.py"
    notebook_path.write_text("def broken(:\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="could not be parsed as Python"):
        _ = notebook_to_toml_content(notebook_path)


def test_notebook_to_toml_rejects_when_no_app_cells_exist(tmp_path: Path) -> None:
    notebook_path = tmp_path / "no_cells.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "app = mo.App()",
            'mo.md("# No Cells")',
            "def helper():",
            "    return 1",
        ],
    )

    with pytest.raises(ConfigError, match="No marimo app cells were found"):
        _ = notebook_to_toml_content(notebook_path)


def test_notebook_to_toml_rejects_when_cells_are_not_mappable(tmp_path: Path) -> None:
    notebook_path = tmp_path / "no_mappable_cells.py"
    _write_notebook(
        notebook_path,
        [
            "import marimo as mo",
            "app = mo.App()",
            'mo.md("# No Mappable Cells")',
            "@app.cell",
            "def helper():",
            '    """Not mapped."""',
            '    mo.md("Some content")',
        ],
    )

    with pytest.raises(ConfigError, match="No mappable specification cells were found"):
        _ = notebook_to_toml_content(notebook_path)
