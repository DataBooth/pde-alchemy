"""Reusable reporting helpers for marimo notebook workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from pdealchemy.config.loader import load_pricing_config
from pdealchemy.config.models import PricingConfig
from pdealchemy.notebook_support import BackendName, NotebookOutputs, prepare_notebook_outputs
from pdealchemy.validation import validate_equation_library
from pdealchemy.validation.equations import EquationLibraryValidationSummary

_EXPLAIN_HEADING_PATTERN = re.compile(r"^#{1,6}\s+PDEAlchemy Explain\s*$", re.IGNORECASE)


class MarimoUIProtocol(Protocol):
    """Subset of marimo UI API used by reporting helpers."""

    def text(self, *, value: str, label: str) -> object:
        """Create a text widget."""
        ...

    def checkbox(self, *, value: bool, label: str) -> object:
        """Create a checkbox widget."""
        ...

    def slider(
        self,
        *,
        start: int | float,
        stop: int | float,
        step: int | float,
        value: int | float,
        label: str,
    ) -> object:
        """Create a slider widget."""
        ...


class MarimoProtocol(Protocol):
    """Subset of marimo module API used by reporting helpers."""

    ui: MarimoUIProtocol

    def md(self, text: str) -> object:
        """Create a markdown view."""
        ...

    def vstack(self, blocks: list[object]) -> object:
        """Create a vertical stack view."""
        ...


class ControlWidgetProtocol(Protocol):
    """UI control protocol exposing a value attribute."""

    value: object


@dataclass(frozen=True)
class NotebookReportControls:
    """Container for UI widgets used by report notebooks."""

    runtime_toml: ControlWidgetProtocol
    equation_library: ControlWidgetProtocol
    compare_backends: ControlWidgetProtocol
    include_pricing: ControlWidgetProtocol
    include_sensitivities: ControlWidgetProtocol
    include_spot_sweep: ControlWidgetProtocol
    include_convergence: ControlWidgetProtocol
    include_validation: ControlWidgetProtocol
    include_explain: ControlWidgetProtocol
    show_tables: ControlWidgetProtocol
    show_charts: ControlWidgetProtocol
    run_analytical: ControlWidgetProtocol
    analytical_tolerance: ControlWidgetProtocol
    spot_sweep_points: ControlWidgetProtocol
    convergence_points: ControlWidgetProtocol


@dataclass(frozen=True)
class NotebookReportSelection:
    """Resolved report options extracted from notebook UI controls."""

    runtime_toml_path: str
    equation_library_path: str
    compare_backends: bool
    include_pricing: bool
    include_sensitivities: bool
    include_spot_sweep: bool
    include_convergence: bool
    include_validation: bool
    include_explain: bool
    show_tables: bool
    show_charts: bool
    run_analytical: bool
    analytical_tolerance: float
    spot_sweep_points: int
    convergence_points: int


@dataclass(frozen=True)
class NotebookReportResult:
    """Notebook report payload used by rendering helpers."""

    outputs: NotebookOutputs
    equation_summary: EquationLibraryValidationSummary | None
    selected_backends: tuple[BackendName, ...]


def create_notebook_report_controls(
    mo: MarimoProtocol,
    *,
    runtime_toml_default: str = "examples/notebooks/black_scholes_pricing.toml",
    equation_library_default: str = "library",
    include_convergence_default: bool = False,
) -> NotebookReportControls:
    """Create the standard control set for report-style notebooks."""
    runtime_toml = mo.ui.text(
        value=runtime_toml_default,
        label="Runtime TOML path",
    )
    equation_library = mo.ui.text(
        value=equation_library_default,
        label="Equation library path",
    )
    compare_backends = mo.ui.checkbox(
        value=True,
        label="Compare QuantLib and py-pde (vanilla only)",
    )
    include_pricing = mo.ui.checkbox(value=True, label="Include pricing report section")
    include_sensitivities = mo.ui.checkbox(value=True, label="Include sensitivities (Greeks)")
    include_spot_sweep = mo.ui.checkbox(value=True, label="Include spot sweep")
    include_convergence = mo.ui.checkbox(
        value=include_convergence_default,
        label="Include convergence report",
    )
    include_validation = mo.ui.checkbox(value=True, label="Include validation summary")
    include_explain = mo.ui.checkbox(value=True, label="Include explain markdown")
    show_tables = mo.ui.checkbox(value=True, label="Show tabular summaries")
    show_charts = mo.ui.checkbox(value=True, label="Show Plotly charts")
    run_analytical = mo.ui.checkbox(value=True, label="Run analytical benchmark")
    analytical_tolerance = mo.ui.slider(
        start=0.05,
        stop=1.5,
        step=0.05,
        value=0.75,
        label="Analytical tolerance",
    )
    spot_sweep_points = mo.ui.slider(
        start=5,
        stop=17,
        step=2,
        value=9,
        label="Spot sweep points",
    )
    convergence_points = mo.ui.slider(
        start=3,
        stop=9,
        step=1,
        value=5,
        label="Convergence points",
    )
    return NotebookReportControls(
        runtime_toml=cast(ControlWidgetProtocol, runtime_toml),
        equation_library=cast(ControlWidgetProtocol, equation_library),
        compare_backends=cast(ControlWidgetProtocol, compare_backends),
        include_pricing=cast(ControlWidgetProtocol, include_pricing),
        include_sensitivities=cast(ControlWidgetProtocol, include_sensitivities),
        include_spot_sweep=cast(ControlWidgetProtocol, include_spot_sweep),
        include_convergence=cast(ControlWidgetProtocol, include_convergence),
        include_validation=cast(ControlWidgetProtocol, include_validation),
        include_explain=cast(ControlWidgetProtocol, include_explain),
        show_tables=cast(ControlWidgetProtocol, show_tables),
        show_charts=cast(ControlWidgetProtocol, show_charts),
        run_analytical=cast(ControlWidgetProtocol, run_analytical),
        analytical_tolerance=cast(ControlWidgetProtocol, analytical_tolerance),
        spot_sweep_points=cast(ControlWidgetProtocol, spot_sweep_points),
        convergence_points=cast(ControlWidgetProtocol, convergence_points),
    )


def render_notebook_report_controls(
    mo: MarimoProtocol,
    controls: NotebookReportControls,
    *,
    title: str,
    description: str,
) -> object:
    """Render report controls in a standard stacked layout."""
    return mo.vstack(
        [
            mo.md(title),
            mo.md(description),
            controls.runtime_toml,
            controls.equation_library,
            controls.compare_backends,
            controls.include_pricing,
            controls.include_sensitivities,
            controls.include_spot_sweep,
            controls.include_convergence,
            controls.include_validation,
            controls.include_explain,
            controls.show_tables,
            controls.show_charts,
            controls.run_analytical,
            controls.analytical_tolerance,
            controls.spot_sweep_points,
            controls.convergence_points,
        ]
    )


def selection_from_controls(controls: NotebookReportControls) -> NotebookReportSelection:
    """Resolve immutable report options from UI controls."""
    runtime_toml_value = cast(str, controls.runtime_toml.value)
    equation_library_value = cast(str, controls.equation_library.value)
    analytical_tolerance_value = cast(float | int | str, controls.analytical_tolerance.value)
    spot_sweep_points_value = cast(int | float | str, controls.spot_sweep_points.value)
    convergence_points_value = cast(int | float | str, controls.convergence_points.value)
    return NotebookReportSelection(
        runtime_toml_path=runtime_toml_value,
        equation_library_path=equation_library_value,
        compare_backends=bool(controls.compare_backends.value),
        include_pricing=bool(controls.include_pricing.value),
        include_sensitivities=bool(controls.include_sensitivities.value),
        include_spot_sweep=bool(controls.include_spot_sweep.value),
        include_convergence=bool(controls.include_convergence.value),
        include_validation=bool(controls.include_validation.value),
        include_explain=bool(controls.include_explain.value),
        show_tables=bool(controls.show_tables.value),
        show_charts=bool(controls.show_charts.value),
        run_analytical=bool(controls.run_analytical.value),
        analytical_tolerance=float(analytical_tolerance_value),
        spot_sweep_points=int(spot_sweep_points_value),
        convergence_points=int(convergence_points_value),
    )


def resolve_report_backends(
    config_data: PricingConfig,
    *,
    compare_backends: bool,
) -> tuple[BackendName, ...]:
    """Resolve report backends based on config and user selection."""
    primary_backend = config_data.numerics.backend
    if compare_backends and config_data.instrument.kind == "vanilla_option":
        ordered = (primary_backend, "quantlib", "py_pde")
        return tuple(dict.fromkeys(ordered))
    return (primary_backend,)


def build_notebook_report(selection: NotebookReportSelection) -> NotebookReportResult:
    """Build report payload from a runtime TOML path and selected options."""
    runtime_toml_path = Path(selection.runtime_toml_path)
    equation_library_path = Path(selection.equation_library_path)
    config_data = load_pricing_config(runtime_toml_path)
    selected_backends = resolve_report_backends(
        config_data,
        compare_backends=selection.compare_backends,
    )
    outputs = prepare_notebook_outputs(
        config_data,
        run_analytical=selection.run_analytical,
        tolerance=selection.analytical_tolerance,
        backends=selected_backends,
        include_greeks=selection.include_sensitivities,
        include_spot_sweep=selection.include_spot_sweep,
        spot_sweep_points=selection.spot_sweep_points,
        include_convergence=selection.include_convergence,
        convergence_points=selection.convergence_points,
    )
    equation_summary = (
        validate_equation_library(equation_library_path) if selection.include_validation else None
    )
    return NotebookReportResult(
        outputs=outputs,
        equation_summary=equation_summary,
        selected_backends=selected_backends,
    )


def clean_explain_markdown(explain_markdown: str) -> str:
    """Remove redundant leading explain headings for cleaner notebook display."""
    lines = explain_markdown.splitlines()
    first_non_empty = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first_non_empty is None:
        return ""
    if _EXPLAIN_HEADING_PATTERN.match(lines[first_non_empty].strip()):
        lines = lines[first_non_empty + 1 :]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def build_report_table_views(
    mo: MarimoProtocol,
    *,
    report: NotebookReportResult | None,
    selection: NotebookReportSelection,
) -> list[object]:
    """Create markdown/table views from notebook report payload."""
    table_views: list[object] = []
    if report is None or not selection.show_tables:
        return table_views

    outputs = report.outputs
    equation_summary = report.equation_summary

    if selection.include_validation and equation_summary is not None:
        analytical_summary = "not run"
        if outputs.analytical_outcome is not None:
            outcome = outputs.analytical_outcome
            analytical_summary = (
                f"{'passed' if outcome.passed else 'failed'} "
                f"(abs error {outcome.absolute_error:.8f}, tolerance {outcome.tolerance:.8f})"
            )
        equation_library_line = (
            "- Equation library: "
            f"{equation_summary.equation_blocks_validated} equation block(s) across "
            f"{equation_summary.files_scanned} file(s)"
        )
        table_views.append(
            mo.md(
                "\n".join(
                    [
                        "## Validation summary",
                        equation_library_line,
                        f"- Analytical benchmark: {analytical_summary}",
                    ]
                )
            )
        )

    if selection.include_pricing:
        pricing_rows = [
            (
                f"| `{backend_name}` | `{result.price:.8f}` | "
                f"`{result.backend}` | `{result.engine}` |"
            )
            for backend_name, result in outputs.pricing_by_backend.items()
        ]
        table_views.append(
            mo.md(
                "\n".join(
                    [
                        "## Pricing table",
                        "| Report backend | Price | Runtime backend | Engine |",
                        "| --- | ---: | --- | --- |",
                        *pricing_rows,
                    ]
                )
            )
        )

    if selection.include_sensitivities:
        if outputs.greeks_by_backend:
            sensitivity_rows = [
                (
                    f"| `{backend_name}` | `{greeks['delta']:.6f}` | "
                    f"`{greeks['gamma']:.6f}` | `{greeks['vega']:.6f}` | "
                    f"`{greeks['rho']:.6f}` | `{greeks['theta']:.6f}` |"
                )
                for backend_name, greeks in outputs.greeks_by_backend.items()
            ]
            table_views.append(
                mo.md(
                    "\n".join(
                        [
                            "## Sensitivities table",
                            "| Backend | Delta | Gamma | Vega | Rho | Theta |",
                            "| --- | ---: | ---: | ---: | ---: | ---: |",
                            *sensitivity_rows,
                        ]
                    )
                )
            )
        else:
            table_views.append(mo.md("## Sensitivities table\n- Not requested for this run."))

    if selection.include_explain:
        explain_body = clean_explain_markdown(outputs.explain_markdown)
        if explain_body:
            table_views.append(
                mo.vstack(
                    [
                        mo.md("## Explain"),
                        mo.md(explain_body),
                    ]
                )
            )
    return table_views


def build_report_chart_views(
    *,
    report: NotebookReportResult | None,
    selection: NotebookReportSelection,
) -> list[object]:
    """Create Plotly chart views from notebook report payload."""
    chart_views: list[object] = []
    if report is None or not selection.show_charts:
        return chart_views

    import plotly.graph_objects as go

    outputs = report.outputs
    if selection.include_pricing:
        pricing_chart = go.Figure()
        pricing_chart.add_bar(
            x=list(outputs.pricing_by_backend.keys()),
            y=[result.price for result in outputs.pricing_by_backend.values()],
        )
        pricing_chart.update_layout(
            title="Pricing by backend",
            xaxis_title="Backend",
            yaxis_title="Option value",
            template="plotly_white",
        )
        chart_views.append(pricing_chart)

    if selection.include_sensitivities and outputs.greeks_by_backend:
        greek_chart = go.Figure()
        greek_names = ["delta", "gamma", "vega", "rho", "theta"]
        for backend_name, greeks in outputs.greeks_by_backend.items():
            greek_chart.add_bar(
                name=backend_name,
                x=greek_names,
                y=[greeks[name] for name in greek_names],
            )
        greek_chart.update_layout(
            title="Sensitivities by backend",
            xaxis_title="Greek",
            yaxis_title="Value",
            barmode="group",
            template="plotly_white",
        )
        chart_views.append(greek_chart)

    if selection.include_spot_sweep and "spot" in outputs.spot_sweep:
        spot_chart = go.Figure()
        for backend_name in outputs.pricing_by_backend:
            price_key = f"{backend_name}:price"
            if price_key in outputs.spot_sweep:
                spot_chart.add_scatter(
                    x=outputs.spot_sweep["spot"],
                    y=outputs.spot_sweep[price_key],
                    mode="lines+markers",
                    name=backend_name,
                )
        spot_chart.update_layout(
            title="Spot sweep",
            xaxis_title="Spot",
            yaxis_title="Option value",
            template="plotly_white",
        )
        chart_views.append(spot_chart)

    if selection.include_convergence and outputs.convergence_sweep:
        convergence_chart = go.Figure()
        for backend_name in outputs.pricing_by_backend:
            price_key = f"{backend_name}:price"
            if price_key in outputs.convergence_sweep:
                convergence_chart.add_scatter(
                    x=outputs.convergence_sweep["time_steps"],
                    y=outputs.convergence_sweep[price_key],
                    mode="lines+markers",
                    name=backend_name,
                )
        convergence_chart.update_layout(
            title="Convergence (price vs time steps)",
            xaxis_title="Time steps",
            yaxis_title="Option value",
            template="plotly_white",
        )
        chart_views.append(convergence_chart)
    return chart_views


def compose_report_view(
    mo: MarimoProtocol,
    *,
    error_view: object | None,
    table_views: list[object],
    chart_views: list[object],
) -> object:
    """Compose final notebook view from table/chart sections and optional errors."""
    if error_view is not None:
        return error_view
    blocks = [*table_views, *chart_views]
    return mo.vstack(blocks) if blocks else mo.md("_No report sections selected._")
