import marimo

__generated_with = "0.22.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import plotly.graph_objects as go

    from pdealchemy.config.loader import load_pricing_config
    from pdealchemy.exceptions import PDEAlchemyError
    from pdealchemy.notebook_support import prepare_notebook_outputs
    from pdealchemy.validation import validate_equation_library

    pathlib_path = Path
    pdealchemy_error = PDEAlchemyError
    return (
        go,
        load_pricing_config,
        mo,
        pdealchemy_error,
        pathlib_path,
        prepare_notebook_outputs,
        validate_equation_library,
    )


@app.cell
def _(mo):
    runtime_toml = mo.ui.text(
        value="examples/notebooks/spec_black_scholes.runtime.toml",
        label="Runtime TOML path",
    )
    equation_library = mo.ui.text(
        value="library",
        label="Equation library path",
    )
    compare_backends = mo.ui.checkbox(
        value=True,
        label="Compare QuantLib and py-pde (vanilla only)",
    )
    include_pricing = mo.ui.checkbox(value=True, label="Include pricing report section")
    include_sensitivities = mo.ui.checkbox(value=True, label="Include sensitivities (Greeks)")
    include_spot_sweep = mo.ui.checkbox(value=True, label="Include spot sweep")
    include_convergence = mo.ui.checkbox(value=False, label="Include convergence report")
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
    mo.vstack(
        [
            mo.md("# Black-Scholes workflow report"),
            mo.md(
                "Select report sections and render mode (tables and/or charts) for "
                "pricing and sensitivities outputs."
            ),
            runtime_toml,
            equation_library,
            compare_backends,
            include_pricing,
            include_sensitivities,
            include_spot_sweep,
            include_convergence,
            include_validation,
            include_explain,
            show_tables,
            show_charts,
            run_analytical,
            analytical_tolerance,
            spot_sweep_points,
            convergence_points,
        ]
    )
    return (
        analytical_tolerance,
        compare_backends,
        convergence_points,
        equation_library,
        include_convergence,
        include_explain,
        include_pricing,
        include_sensitivities,
        include_spot_sweep,
        include_validation,
        run_analytical,
        runtime_toml,
        show_charts,
        show_tables,
        spot_sweep_points,
    )


@app.cell
def _(
    analytical_tolerance,
    compare_backends,
    convergence_points,
    equation_library,
    include_convergence,
    include_sensitivities,
    include_spot_sweep,
    include_validation,
    load_pricing_config,
    mo,
    pdealchemy_error,
    pathlib_path,
    prepare_notebook_outputs,
    run_analytical,
    runtime_toml,
    spot_sweep_points,
    validate_equation_library,
):
    error_view = None
    outputs = None
    equation_summary = None
    selected_backends: tuple[str, ...] = ("quantlib",)
    try:
        runtime_path = pathlib_path(runtime_toml.value)
        library_path = pathlib_path(equation_library.value)
        config_data = load_pricing_config(runtime_path)

        if compare_backends.value and config_data.instrument.kind == "vanilla_option":
            selected_backends = ("quantlib", "py_pde")

        outputs = prepare_notebook_outputs(
            config_data,
            run_analytical=run_analytical.value,
            tolerance=analytical_tolerance.value,
            backends=selected_backends,
            include_greeks=include_sensitivities.value,
            include_spot_sweep=include_spot_sweep.value,
            spot_sweep_points=spot_sweep_points.value,
            include_convergence=include_convergence.value,
            convergence_points=convergence_points.value,
        )

        if include_validation.value:
            equation_summary = validate_equation_library(library_path)
    except pdealchemy_error as error:
        error_view = mo.md(
            f"**Error:** {error.message}\n\n{error.details or ''}\n\n{error.suggestion or ''}"
        )
    return equation_summary, error_view, outputs, selected_backends


@app.cell
def _(
    equation_summary,
    include_explain,
    include_pricing,
    include_sensitivities,
    include_validation,
    mo,
    outputs,
    show_tables,
):
    table_views: list[object] = []
    if outputs is not None and show_tables.value:
        if include_validation.value and equation_summary is not None:
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

        if include_pricing.value:
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

        if include_sensitivities.value:
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

        if include_explain.value:
            table_views.append(
                mo.vstack(
                    [
                        mo.md("## Explain (markdown)"),
                        mo.md(outputs.explain_markdown),
                    ]
                )
            )
    return (table_views,)


@app.cell
def _(
    go,
    include_convergence,
    include_pricing,
    include_sensitivities,
    include_spot_sweep,
    outputs,
    show_charts,
):
    chart_views: list[object] = []
    if outputs is not None and show_charts.value:
        if include_pricing.value:
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

        if include_sensitivities.value and outputs.greeks_by_backend:
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

        if include_spot_sweep.value and "spot" in outputs.spot_sweep:
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

        if include_convergence.value and outputs.convergence_sweep:
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

    return (chart_views,)


@app.cell
def _(error_view, mo, table_views, chart_views):
    if error_view is not None:
        view = error_view
    else:
        blocks = [*table_views, *chart_views]
        view = mo.vstack(blocks) if blocks else mo.md("_No report sections selected._")
    view  # noqa: B018
    return


if __name__ == "__main__":
    app.run()
