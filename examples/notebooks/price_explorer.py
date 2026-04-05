import marimo

__generated_with = "0.22.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import plotly.graph_objects as go

    from pdealchemy.exceptions import PDEAlchemyError
    from pdealchemy.notebook_support import (
        canonical_example_paths,
        load_canonical_example,
        prepare_notebook_outputs,
        repository_root_from_notebook,
        with_monte_carlo_paths,
    )

    return (
        PDEAlchemyError,
        Path,
        canonical_example_paths,
        go,
        load_canonical_example,
        mo,
        prepare_notebook_outputs,
        repository_root_from_notebook,
        with_monte_carlo_paths,
    )


@app.cell
def _(mo):
    example = mo.ui.dropdown(
        options={
            "Vanilla European call": "vanilla",
            "Exotic discrete Asian + barrier + dividends": "exotic",
        },
        value="vanilla",
        label="Example configuration",
    )
    compare_backends = mo.ui.checkbox(
        value=True,
        label="Compare QuantLib and py-pde (vanilla only)",
    )
    include_greeks = mo.ui.checkbox(
        value=True,
        label="Estimate Greeks (finite differences)",
    )
    include_spot_sweep = mo.ui.checkbox(
        value=True,
        label="Build spot sweep Plotly chart",
    )
    spot_sweep_points = mo.ui.slider(
        start=5,
        stop=17,
        step=2,
        value=9,
        label="Spot sweep points",
    )
    run_analytical = mo.ui.checkbox(
        value=True,
        label="Run analytical benchmark",
    )
    tolerance = mo.ui.slider(
        start=0.05,
        stop=1.5,
        step=0.05,
        value=0.75,
        label="Analytical tolerance",
    )
    monte_carlo_paths = mo.ui.slider(
        start=2000,
        stop=40000,
        step=1000,
        value=5000,
        label="Exotic Monte Carlo paths",
    )
    mo.vstack(
        [
            mo.md("## PDEAlchemy pricing explorer"),
            mo.md(
                "Use this notebook to compare backend prices, inspect Greeks, "
                "and visualise spot sensitivity."
            ),
            example,
            compare_backends,
            include_greeks,
            include_spot_sweep,
            spot_sweep_points,
            run_analytical,
            tolerance,
            monte_carlo_paths,
        ]
    )
    return (
        compare_backends,
        example,
        include_greeks,
        include_spot_sweep,
        monte_carlo_paths,
        run_analytical,
        spot_sweep_points,
        tolerance,
    )


@app.cell
def _(
    compare_backends,
    PDEAlchemyError,
    Path,
    canonical_example_paths,
    example,
    go,
    include_greeks,
    include_spot_sweep,
    load_canonical_example,
    mo,
    monte_carlo_paths,
    prepare_notebook_outputs,
    repository_root_from_notebook,
    run_analytical,
    spot_sweep_points,
    tolerance,
    with_monte_carlo_paths,
):
    repo_root = repository_root_from_notebook(Path(__file__))
    selected = example.value
    config_data = load_canonical_example(selected, repo_root=repo_root)
    if selected == "exotic":
        config_data = with_monte_carlo_paths(config_data, monte_carlo_paths.value)

    examples = canonical_example_paths(repo_root)
    path_summary = (
        f"- vanilla: `{examples['vanilla']}`\n"
        f"- exotic: `{examples['exotic']}`"
    )

    try:
        selected_backends = ("quantlib", "py_pde")
        if selected != "vanilla" or not compare_backends.value:
            selected_backends = ("quantlib",)

        include_greeks_now = include_greeks.value and selected == "vanilla"
        include_spot_sweep_now = include_spot_sweep.value and selected == "vanilla"
        outputs = prepare_notebook_outputs(
            config_data,
            run_analytical=run_analytical.value,
            tolerance=tolerance.value,
            backends=selected_backends,
            include_greeks=include_greeks_now,
            include_spot_sweep=include_spot_sweep_now,
            spot_sweep_points=spot_sweep_points.value,
        )

        analytical_summary = "not run"
        if outputs.analytical_outcome is not None:
            outcome = outputs.analytical_outcome
            analytical_summary = (
                f"{'passed' if outcome.passed else 'failed'} "
                f"(abs error {outcome.absolute_error:.8f}, "
                f"tolerance {outcome.tolerance:.8f})"
            )

        backend_lines = []
        for backend, result in outputs.pricing_by_backend.items():
            backend_lines.append(
                f"- `{backend}`: `{result.price:.8f}` using `{result.engine}`"
            )
        backend_summary = "\n".join(backend_lines)

        greek_lines = []
        for backend, greek_values in outputs.greeks_by_backend.items():
            greek_lines.append(
                f"- `{backend}`: "
                f"Δ `{greek_values['delta']:.6f}`, "
                f"Γ `{greek_values['gamma']:.6f}`, "
                f"Vega `{greek_values['vega']:.6f}`, "
                f"Rho `{greek_values['rho']:.6f}`, "
                f"Theta `{greek_values['theta']:.6f}`"
            )
        greek_summary = (
            "\n".join(greek_lines)
            if greek_lines
            else "- Greeks not requested for this selection."
        )

        price_bar = go.Figure()
        price_bar.add_bar(
            x=list(outputs.pricing_by_backend.keys()),
            y=[result.price for result in outputs.pricing_by_backend.values()],
            marker_color=["#2E86AB", "#F18F01"],
        )
        price_bar.update_layout(
            title="Backend price comparison",
            xaxis_title="Backend",
            yaxis_title="Option value",
            template="plotly_white",
        )

        sweep_plot = None
        if "spot" in outputs.spot_sweep:
            sweep_plot = go.Figure()
            spot_values = outputs.spot_sweep["spot"]
            for backend in selected_backends:
                key = f"{backend}:price"
                if key in outputs.spot_sweep:
                    sweep_plot.add_scatter(
                        x=spot_values,
                        y=outputs.spot_sweep[key],
                        mode="lines+markers",
                        name=backend,
                    )
            sweep_plot.update_layout(
                title="Spot sweep price profile",
                xaxis_title="Spot",
                yaxis_title="Option value",
                template="plotly_white",
            )

        notebook_notes = ""
        if selected != "vanilla":
            notebook_notes = (
                "\n\n### Notes\n"
                "- Dual-backend comparison and Greeks are enabled for vanilla routes.\n"
                "- Exotic routes currently run through QuantLib only."
            )

        summary = mo.md(
            "### Canonical config paths\n"
            f"{path_summary}\n\n"
            "### Pricing summary\n"
            f"{backend_summary}\n\n"
            "### Greeks\n"
            f"{greek_summary}\n\n"
            "### Analytical benchmark\n"
            f"- {analytical_summary}"
            f"{notebook_notes}\n"
        )
        view = mo.vstack(
            [
                summary,
                price_bar,
                sweep_plot if sweep_plot is not None else mo.md(""),
                mo.md("### Explain output"),
                mo.md(outputs.explain_markdown),
            ]
        )
    except PDEAlchemyError as error:
        error_text = (
            f"**Error:** {error.message}\n\n"
            f"{error.details or ''}\n\n"
            f"{error.suggestion or ''}"
        )
        view = mo.md(error_text)
    view
    return


if __name__ == "__main__":
    app.run()
