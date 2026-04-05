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
        include_greeks,
        include_convergence,
        include_spot_sweep,
        monte_carlo_paths,
        repo_root,
        runtime_profile,
        runtime_profile_options,
        run_analytical,
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
    example_options,
    go,
    include_greeks,
    include_convergence,
    include_spot_sweep,
    load_canonical_example,
    mo,
    monte_carlo_paths,
    prepare_notebook_outputs,
    repo_root,
    resolve_canonical_example_selection,
    runtime_profile,
    runtime_profile_options,
    run_analytical,
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

    try:
        selected_backends = ("quantlib", "py_pde")
        if selected != "vanilla" or not compare_backends.value:
            selected_backends = ("quantlib",)

        include_greeks_now = include_greeks.value and selected == "vanilla"
        include_spot_sweep_now = include_spot_sweep.value and selected == "vanilla"
        include_convergence_now = include_convergence.value and selected == "vanilla"
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

        analytical_summary = "not run"
        if outputs.analytical_outcome is not None:
            outcome = outputs.analytical_outcome
            analytical_summary = (
                f"{'passed' if outcome.passed else 'failed'} "
                f"(abs error {outcome.absolute_error:.8f}, "
                f"tolerance {outcome.tolerance:.8f})"
            )

        pricing_rows = [
            f"| `{backend}` | `{result.price:.8f}` | `{result.engine}` |"
            for backend, result in outputs.pricing_by_backend.items()
        ]
        if len(outputs.pricing_by_backend) > 1:
            backend_prices = [result.price for result in outputs.pricing_by_backend.values()]
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
                    f"| `{backend}` | "
                    f"`{greek_values['delta']:.6f}` | "
                    f"`{greek_values['gamma']:.6f}` | "
                    f"`{greek_values['vega']:.6f}` | "
                    f"`{greek_values['rho']:.6f}` | "
                    f"`{greek_values['theta']:.6f}` |"
                )
                for backend, greek_values in outputs.greeks_by_backend.items()
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

        price_bar = go.Figure()
        price_bar.add_bar(
            x=list(outputs.pricing_by_backend.keys()),
            y=[result.price for result in outputs.pricing_by_backend.values()],
            marker_color=["#2E86AB", "#F18F01", "#6A4C93"][
                : len(outputs.pricing_by_backend)
            ],
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

        convergence_price_plot = None
        convergence_error_plot = None
        if outputs.convergence_sweep:
            time_steps = outputs.convergence_sweep["time_steps"]
            space_steps = outputs.convergence_sweep["space_steps"]

            convergence_price_plot = go.Figure()
            for backend in selected_backends:
                key = f"{backend}:price"
                if key in outputs.convergence_sweep:
                    convergence_price_plot.add_scatter(
                        x=time_steps,
                        y=outputs.convergence_sweep[key],
                        customdata=space_steps,
                        mode="lines+markers",
                        name=backend,
                        hovertemplate=(
                            "time steps=%{x:.0f}<br>"
                            "space steps=%{customdata:.0f}<br>"
                            "price=%{y:.8f}<extra></extra>"
                        ),
                    )
            convergence_price_plot.update_layout(
                title="Resolution convergence: price vs time steps",
                xaxis_title="Time steps",
                yaxis_title="Option value",
                template="plotly_white",
            )

            convergence_error_plot = go.Figure()
            for backend in selected_backends:
                key = f"{backend}:abs_error"
                if key in outputs.convergence_sweep:
                    convergence_error_plot.add_scatter(
                        x=time_steps,
                        y=[max(value, 1e-12) for value in outputs.convergence_sweep[key]],
                        customdata=space_steps,
                        mode="lines+markers",
                        name=f"{backend} abs error",
                        hovertemplate=(
                            "time steps=%{x:.0f}<br>"
                            "space steps=%{customdata:.0f}<br>"
                            "abs error=%{y:.8e}<extra></extra>"
                        ),
                    )
            if "backend_abs_diff" in outputs.convergence_sweep:
                convergence_error_plot.add_scatter(
                    x=time_steps,
                    y=[
                        max(value, 1e-12)
                        for value in outputs.convergence_sweep["backend_abs_diff"]
                    ],
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
        view_blocks = [summary, price_bar]
        if sweep_plot is not None:
            view_blocks.append(sweep_plot)
        if convergence_price_plot is not None:
            view_blocks.append(convergence_price_plot)
        if convergence_error_plot is not None:
            view_blocks.append(convergence_error_plot)
        view_blocks.extend(
            [
                mo.md("### Explain output"),
                mo.md(outputs.explain_markdown),
            ]
        )
        view = mo.vstack(view_blocks)
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
