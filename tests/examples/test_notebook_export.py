"""Notebook execution smoke tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_EXAMPLE = REPO_ROOT / "examples" / "notebooks" / "price_explorer.py"


def test_price_explorer_notebook_exports_to_html(tmp_path: Path) -> None:
    output_html = tmp_path / "price_explorer.html"
    command = [
        sys.executable,
        "-m",
        "marimo",
        "export",
        "html",
        str(NOTEBOOK_EXAMPLE),
        "-o",
        str(output_html),
        "-f",
    ]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Notebook export failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert output_html.exists()
