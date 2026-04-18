import marimo

__generated_with = "0.22.4"
app = marimo.App(width="medium")


@app.cell
def _():

    import marimo as mo

    from pdealchemy.exceptions import PDEAlchemyError
    from pdealchemy.notebook_reporting import (
        build_notebook_report,
        build_report_chart_views,
        build_report_table_views,
        compose_report_view,
        create_notebook_report_controls,
        render_notebook_report_controls,
        selection_from_controls,
    )

    pdealchemy_error = PDEAlchemyError
    return (
        build_notebook_report,
        build_report_chart_views,
        build_report_table_views,
        compose_report_view,
        create_notebook_report_controls,
        mo,
        pdealchemy_error,
        render_notebook_report_controls,
        selection_from_controls,
    )


@app.cell
def _(create_notebook_report_controls, mo, render_notebook_report_controls):
    controls = create_notebook_report_controls(
        mo,
        runtime_toml_default="examples/notebooks/spec_black_scholes.runtime.toml",
        equation_library_default="library",
    )
    render_notebook_report_controls(
        mo,
        controls,
        title="# Black-Scholes workflow report",
        description=(
            "Select report sections and render mode (tables and/or charts) for pricing "
            "and sensitivities outputs."
        ),
    )
    return (controls,)


@app.cell
def _(
    build_notebook_report,
    controls,
    mo,
    pdealchemy_error,
    selection_from_controls,
):
    error_view = None
    report = None
    selection = selection_from_controls(controls)
    try:
        report = build_notebook_report(selection)
    except pdealchemy_error as error:
        error_view = mo.md(
            f"**Error:** {error.message}\n\n{error.details or ''}\n\n{error.suggestion or ''}"
        )
    return error_view, report, selection


@app.cell
def _(
    build_report_table_views,
    mo,
    report,
    selection,
):
    table_views = build_report_table_views(
        mo,
        report=report,
        selection=selection,
    )
    return (table_views,)


@app.cell
def _(
    build_report_chart_views,
    report,
    selection,
):
    chart_views = build_report_chart_views(
        report=report,
        selection=selection,
    )

    return (chart_views,)


@app.cell
def _(chart_views, compose_report_view, error_view, mo, table_views):
    view = compose_report_view(
        mo,
        error_view=error_view,
        table_views=table_views,
        chart_views=chart_views,
    )
    view  # noqa: B018
    return


if __name__ == "__main__":
    app.run()
