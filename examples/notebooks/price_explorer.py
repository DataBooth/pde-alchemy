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
        apply_interactive_profile,
        canonical_example_paths,
        canonical_example_dropdown_options,
        default_canonical_example_label,
        load_canonical_example,
        prepare_notebook_outputs,
        resolve_canonical_example_selection,
        repository_root_from_notebook,
        with_monte_carlo_paths,
    )

    return (
        PDEAlchemyError,
        Path,
        apply_interactive_profile,
        canonical_example_dropdown_options,
        canonical_example_paths,
        default_canonical_example_label,
        go,
        load_canonical_example,
        mo,
        prepare_notebook_outputs,
        repository_root_from_notebook,
        resolve_canonical_example_selection,
        with_monte_carlo_paths,
    )


@app.cell
def _(
    Path,
    canonical_example_dropdown_options,
    default_canonical_example_label,
    mo,
    repository_root_from_notebook,
):
    repo_root = repository_root_from_notebook(Path(__file__))
    example_options = canonical_example_dropdown_options(repo_root)
    default_example_label = default_canonical_example_label(repo_root)
    example = mo.ui.dropdown(
        options=example_options,
        value=default_example_label,
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
    include_convergence = mo.ui.checkbox(
        value=False,
        label="Build convergence plots (vanilla only)",
    )
    convergence_points = mo.ui.slider(
        start=3,
        stop=9,
        step=1,
        value=5,
        label="Convergence sweep points",
    )
    runtime_profile_options = {
        "Fast preview (lower numerics)": "fast",
        "Balanced": "balanced",
        "Accurate (full numerics)": "accurate",
    }
    runtime_profile = mo.ui.dropdown(
        options=runtime_profile_options,
        value="Balanced",
        label="Runtime profile",
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
            mo.md(
                "### What this workbook does\n"
                "- Loads a canonical pricing configuration (vanilla or exotic).\n"
                "- Prices the route with one or more backends.\n"
                "- Optionally computes Greeks, spot sweeps, and convergence diagnostics."
            ),
            mo.md(
                "### Why this workbook exists\n"
                "- Gives a fast, visual way to compare numerical behaviour across backends.\n"
                "- Helps validate price quality versus numerical resolution.\n"
                "- Supports quick experimentation before locking down production settings."
            ),
            mo.md(
                "### How to use it\n"
                "1. Start with `fast` or `balanced` runtime profile while iterating.\n"
                "2. Enable convergence plots to inspect numerical stability and drift.\n"
                "3. Switch to `accurate` profile for final comparison values."
            ),
            example,
            compare_backends,
            include_greeks,
            include_spot_sweep,
            include_convergence,
            convergence_points,
            runtime_profile,
            spot_sweep_points,
            run_analytical,
            tolerance,
            monte_carlo_paths,
        ]
    )
    return (
        compare_backends,
        convergence_points,
        example,
        example_options,
        include_convergence,
        include_greeks,
        include_spot_sweep,
        monte_carlo_paths,
        repo_root,
        run_analytical,
        runtime_profile,
        runtime_profile_options,
        spot_sweep_points,
        tolerance,
    )


@app.cell
def _(
    PDEAlchemyError,
    apply_interactive_profile,
    canonical_example_paths,
    compare_backends,
    convergence_points,
    example,
    include_convergence,
    include_greeks,
    include_spot_sweep,
    load_canonical_example,
    mo,
    monte_carlo_paths,
    prepare_notebook_outputs,
    repo_root,
    resolve_canonical_example_selection,
    run_analytical,
    runtime_profile,
    runtime_profile_options,
    spot_sweep_points,
    tolerance,
    with_monte_carlo_paths,
):
    selected = resolve_canonical_example_selection(example.value, repo_root=repo_root)
    config_data = load_canonical_example(selected, repo_root=repo_root)
    if selected == "exotic":
        config_data = with_monte_carlo_paths(config_data, monte_carlo_paths.value)
    selected_runtime_profile = runtime_profile_options.get(
        runtime_profile.value,
        runtime_profile.value,
    )
    config_data = apply_interactive_profile(config_data, selected_runtime_profile)

    examples = canonical_example_paths(repo_root)
    path_summary = (
        f"- vanilla: `{examples['vanilla']}`\n"
        f"- exotic: `{examples['exotic']}`"
    )
    selected_backends = ("quantlib", "py_pde")
    if selected != "vanilla" or not compare_backends.value:
        selected_backends = ("quantlib",)

    include_greeks_now = include_greeks.value and selected == "vanilla"
    include_spot_sweep_now = include_spot_sweep.value and selected == "vanilla"
    include_convergence_now = include_convergence.value and selected == "vanilla"
    error_view = None
    outputs = None
    try:
        outputs = prepare_notebook_outputs(
            config_data,
            run_analytical=run_analytical.value,
            tolerance=tolerance.value,
            backends=selected_backends,
            include_greeks=include_greeks_now,
            include_spot_sweep=include_spot_sweep_now,
            spot_sweep_points=spot_sweep_points.value,
            include_convergence=include_convergence_now,
            convergence_points=convergence_points.value,
        )
    except PDEAlchemyError as error:
        error_text = (
            f"**Error:** {error.message}\n\n"
            f"{error.details or ''}\n\n"
            f"{error.suggestion or ''}"
        )
        error_view = mo.md(error_text)
    return (
        error_view,
        outputs,
        path_summary,
        selected,
        selected_runtime_profile,
    )


@app.cell
def _(
    example,
    example_options,
    include_convergence,
    mo,
    outputs,
    path_summary,
    selected,
    selected_runtime_profile,
):
    summary = None
    if outputs is not None:
        analytical_summary = "not run"
        if outputs.analytical_outcome is not None:
            outcome = outputs.analytical_outcome
            analytical_summary = (
                f"{'passed' if outcome.passed else 'failed'} "
                f"(abs error {outcome.absolute_error:.8f}, "
                f"tolerance {outcome.tolerance:.8f})"
            )

        pricing_rows = [
            f"| `{summary_backend_name}` | `{summary_result.price:.8f}` | `{summary_result.engine}` |"
            for summary_backend_name, summary_result in outputs.pricing_by_backend.items()
        ]
        if len(outputs.pricing_by_backend) > 1:
            backend_prices = [
                summary_result.price for summary_result in outputs.pricing_by_backend.values()
            ]
            spread = max(backend_prices) - min(backend_prices)
            pricing_rows.append(f"| `spread (max-min)` | `{spread:.8f}` | `-` |")
        pricing_summary = "\n".join(
            [
                "| Backend | Price | Engine |",
                "| --- | ---: | --- |",
                *pricing_rows,
            ]
        )

        if outputs.greeks_by_backend:
            greek_rows = [
                (
                    f"| `{summary_greek_backend_name}` | "
                    f"`{summary_greek_values['delta']:.6f}` | "
                    f"`{summary_greek_values['gamma']:.6f}` | "
                    f"`{summary_greek_values['vega']:.6f}` | "
                    f"`{summary_greek_values['rho']:.6f}` | "
                    f"`{summary_greek_values['theta']:.6f}` |"
                )
                for summary_greek_backend_name, summary_greek_values in outputs.greeks_by_backend.items()
            ]
            greek_summary = "\n".join(
                [
                    "| Backend | Delta | Gamma | Vega | Rho | Theta |",
                    "| --- | ---: | ---: | ---: | ---: | ---: |",
                    *greek_rows,
                ]
            )
        else:
            greek_summary = "- Greeks not requested for this selection."

        notebook_notes = (
            "\n\n### Runtime notes\n"
            f"- Runtime profile: `{selected_runtime_profile}`.\n"
            "- Use `fast` while tuning controls, then switch to `accurate` for final values."
        )
        if selected != "vanilla":
            notebook_notes = (
                f"{notebook_notes}\n"
                "- Dual-backend comparison and Greeks are enabled for vanilla routes.\n"
                "- Exotic routes currently run through QuantLib only."
            )
        if include_convergence.value and selected != "vanilla":
            notebook_notes = (
                f"{notebook_notes}\n"
                "- Convergence plots are currently enabled for vanilla routes only."
            )
        if example.value not in example_options:
            notebook_notes = (
                f"{notebook_notes}\n"
                "- Selection was normalised from a non-standard dropdown value."
            )

        summary = mo.md(
            "### Canonical config paths\n"
            f"{path_summary}\n\n"
            "### Pricing summary\n"
            f"{pricing_summary}\n\n"
            "### Greeks\n"
            f"{greek_summary}\n\n"
            "### Analytical benchmark\n"
            f"- {analytical_summary}"
            f"{notebook_notes}\n"
        )
    return (summary,)


@app.cell
def _(go, outputs):
    price_bar = None

    sweep_plot = None
    if outputs is not None:
        price_bar = go.Figure()
        price_bar.add_bar(
            x=list(outputs.pricing_by_backend.keys()),
            y=[result.price for result in outputs.pricing_by_backend.values()],
            marker_color=["#2E86AB", "#F18F01", "#6A4C93"][: len(outputs.pricing_by_backend)],
        )
        price_bar.update_layout(
            title="Backend price comparison",
            xaxis_title="Backend",
            yaxis_title="Option value",
            template="plotly_white",
        )

        if "spot" in outputs.spot_sweep:
            sweep_plot = go.Figure()
            spot_values = outputs.spot_sweep["spot"]
            for spot_backend_name in outputs.pricing_by_backend:
                spot_price_key = f"{spot_backend_name}:price"
                if spot_price_key in outputs.spot_sweep:
                    sweep_plot.add_scatter(
                        x=spot_values,
                        y=outputs.spot_sweep[spot_price_key],
                        mode="lines+markers",
                        name=spot_backend_name,
                    )
            sweep_plot.update_layout(
                title="Spot sweep price profile",
                xaxis_title="Spot",
                yaxis_title="Option value",
                template="plotly_white",
            )
    return price_bar, sweep_plot


@app.cell
def _(go, outputs):
    convergence_time_plot = None

    convergence_mesh_plot = None
    convergence_error_plot = None
    if outputs is not None and outputs.convergence_sweep:
        time_steps = outputs.convergence_sweep["time_steps"]
        space_steps = outputs.convergence_sweep["space_steps"]
        mesh_size = outputs.convergence_sweep.get("mesh_size", [])

        convergence_time_plot = go.Figure()
        for conv_time_backend_name in outputs.pricing_by_backend:
            conv_time_price_key = f"{conv_time_backend_name}:price"
            if conv_time_price_key in outputs.convergence_sweep:
                convergence_time_plot.add_scatter(
                    x=time_steps,
                    y=outputs.convergence_sweep[conv_time_price_key],
                    customdata=space_steps,
                    mode="lines+markers",
                    name=conv_time_backend_name,
                    hovertemplate=(
                        "time steps=%{x:.0f}<br>"
                        "space steps=%{customdata:.0f}<br>"
                        "price=%{y:.8f}<extra></extra>"
                    ),
                )
        convergence_time_plot.update_layout(
            title="Resolution convergence: price vs time steps",
            xaxis_title="Time steps",
            yaxis_title="Option value",
            template="plotly_white",
        )

        if mesh_size:
            mesh_customdata = [
                [time_step, space_step]
                for time_step, space_step in zip(time_steps, space_steps, strict=False)
            ]
            convergence_mesh_plot = go.Figure()
            for conv_mesh_backend_name in outputs.pricing_by_backend:
                conv_mesh_price_key = f"{conv_mesh_backend_name}:price"
                if conv_mesh_price_key in outputs.convergence_sweep:
                    convergence_mesh_plot.add_scatter(
                        x=mesh_size,
                        y=outputs.convergence_sweep[conv_mesh_price_key],
                        customdata=mesh_customdata,
                        mode="lines+markers",
                        name=conv_mesh_backend_name,
                        hovertemplate=(
                            "mesh size ΔS=%{x:.6f}<br>"
                            "time steps=%{customdata[0]:.0f}<br>"
                            "space steps=%{customdata[1]:.0f}<br>"
                            "price=%{y:.8f}<extra></extra>"
                        ),
                    )
            convergence_mesh_plot.update_layout(
                title="Resolution convergence: price vs mesh size",
                xaxis_title="Mesh size (ΔS)",
                yaxis_title="Option value",
                template="plotly_white",
            )

        convergence_error_plot = go.Figure()
        for conv_error_backend_name in outputs.pricing_by_backend:
            conv_error_key = f"{conv_error_backend_name}:abs_error"
            if conv_error_key in outputs.convergence_sweep:
                convergence_error_plot.add_scatter(
                    x=time_steps,
                    y=[max(value, 1e-12) for value in outputs.convergence_sweep[conv_error_key]],
                    customdata=space_steps,
                    mode="lines+markers",
                    name=f"{conv_error_backend_name} abs error",
                    hovertemplate=(
                        "time steps=%{x:.0f}<br>"
                        "space steps=%{customdata:.0f}<br>"
                        "abs error=%{y:.8e}<extra></extra>"
                    ),
                )
        if "backend_abs_diff" in outputs.convergence_sweep:
            convergence_error_plot.add_scatter(
                x=time_steps,
                y=[max(value, 1e-12) for value in outputs.convergence_sweep["backend_abs_diff"]],
                customdata=space_steps,
                mode="lines+markers",
                line={"dash": "dash"},
                name="backend abs diff",
                hovertemplate=(
                    "time steps=%{x:.0f}<br>"
                    "space steps=%{customdata:.0f}<br>"
                    "abs diff=%{y:.8e}<extra></extra>"
                ),
            )
        convergence_error_plot.update_layout(
            title="Resolution convergence: error trend",
            xaxis_title="Time steps",
            yaxis_title="Absolute error",
            yaxis_type="log",
            template="plotly_white",
        )
    return convergence_error_plot, convergence_mesh_plot, convergence_time_plot


@app.cell
def _(mo, outputs):
    explain_view = None
    if outputs is not None:
        explain_view = mo.vstack(
            [
                mo.md("### Explain output"),
                mo.md(outputs.explain_markdown),
            ]
        )
    return (explain_view,)


@app.cell
def _(
    convergence_error_plot,
    convergence_mesh_plot,
    convergence_time_plot,
    error_view,
    explain_view,
    mo,
    price_bar,
    summary,
    sweep_plot,
):
    if error_view is not None:
        view = error_view
    else:
        view_blocks = []
        if summary is not None:
            view_blocks.append(summary)
        for block in (
            price_bar,
            sweep_plot,
            convergence_time_plot,
            convergence_mesh_plot,
            convergence_error_plot,
            explain_view,
        ):
            if block is not None:
                view_blocks.append(block)
        view = mo.vstack(view_blocks) if view_blocks else mo.md("")
    view
    return


if __name__ == "__main__":
    app.run()
