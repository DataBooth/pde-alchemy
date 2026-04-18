"""Tests for reusable notebook reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass

from pdealchemy.core import PricingResult
from pdealchemy.notebook_reporting import (
    NotebookReportResult,
    NotebookReportSelection,
    build_report_chart_views,
    build_report_table_views,
    clean_explain_markdown,
    resolve_report_backends,
)
from pdealchemy.notebook_support import NotebookOutputs
from pdealchemy.validation.equations import EquationLibraryValidationSummary
from pdealchemy.validation.runner import ValidationOutcome


@dataclass(frozen=True)
class _MockNumerics:
    backend: str


@dataclass(frozen=True)
class _MockInstrument:
    kind: str


@dataclass(frozen=True)
class _MockConfig:
    numerics: _MockNumerics
    instrument: _MockInstrument


class _MockMo:
    def md(self, text: str):
        return ("md", text)

    def vstack(self, blocks: list[object]):
        return ("vstack", blocks)


def _selection(**overrides):
    defaults = {
        "runtime_toml_path": "examples/notebooks/spec_black_scholes.runtime.toml",
        "equation_library_path": "library",
        "compare_backends": True,
        "include_pricing": True,
        "include_sensitivities": True,
        "include_spot_sweep": True,
        "include_convergence": True,
        "include_validation": True,
        "include_explain": True,
        "show_tables": True,
        "show_charts": True,
        "run_analytical": True,
        "analytical_tolerance": 0.75,
        "spot_sweep_points": 9,
        "convergence_points": 5,
    }
    defaults.update(overrides)
    return NotebookReportSelection(**defaults)


def _sample_report():
    validation_outcome = ValidationOutcome(
        name="analytical_black_scholes",
        passed=True,
        model_price=10.51,
        benchmark_price=10.50,
        absolute_error=0.01,
        tolerance=0.75,
    )
    pricing_by_backend = {
        "quantlib": PricingResult(price=10.51, backend="quantlib", engine="FdEngine"),
        "py_pde": PricingResult(price=10.48, backend="py_pde", engine="FiniteDifference"),
    }
    outputs = NotebookOutputs(
        pricing_result=pricing_by_backend["quantlib"],
        pricing_by_backend=pricing_by_backend,
        explain_markdown="# PDEAlchemy Explain\n\n## Model\nCore explain content.",
        analytical_outcome=validation_outcome,
        greeks_by_backend={
            "quantlib": {
                "delta": 0.5,
                "gamma": 0.02,
                "vega": 0.18,
                "rho": 0.22,
                "theta": -0.03,
            },
            "py_pde": {
                "delta": 0.49,
                "gamma": 0.021,
                "vega": 0.179,
                "rho": 0.219,
                "theta": -0.031,
            },
        },
        spot_sweep={
            "spot": [70.0, 100.0, 130.0],
            "quantlib:price": [1.2, 10.5, 33.8],
            "py_pde:price": [1.1, 10.4, 33.7],
        },
        convergence_sweep={
            "time_steps": [80.0, 160.0, 320.0],
            "quantlib:price": [10.3, 10.45, 10.51],
            "py_pde:price": [10.2, 10.42, 10.48],
        },
    )
    return NotebookReportResult(
        outputs=outputs,
        equation_summary=EquationLibraryValidationSummary(
            files_scanned=4,
            equation_blocks_validated=11,
        ),
        selected_backends=("quantlib", "py_pde"),
    )


def test_clean_explain_markdown_removes_redundant_heading():
    markdown_text = "# PDEAlchemy Explain\n\n## Model\nBody."
    cleaned = clean_explain_markdown(markdown_text)

    assert cleaned == "## Model\nBody."


def test_resolve_report_backends_keeps_primary_order_for_comparison():
    config_data = _MockConfig(
        numerics=_MockNumerics(backend="py_pde"),
        instrument=_MockInstrument(kind="vanilla_option"),
    )

    selected_backends = resolve_report_backends(config_data, compare_backends=True)

    assert selected_backends == ("py_pde", "quantlib")


def test_build_report_table_views_shows_clean_explain_section():
    report = _sample_report()
    views = build_report_table_views(
        _MockMo(),
        report=report,
        selection=_selection(),
    )

    explain_view = views[-1]
    assert explain_view[0] == "vstack"
    assert explain_view[1][0] == ("md", "## Explain")
    assert explain_view[1][1] == ("md", "## Model\nCore explain content.")


def test_build_report_chart_views_renders_selected_charts():
    report = _sample_report()
    charts = build_report_chart_views(
        report=report,
        selection=_selection(),
    )

    assert len(charts) == 4
