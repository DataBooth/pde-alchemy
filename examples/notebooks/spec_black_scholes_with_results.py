import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def notebook_context():
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
    from pdealchemy.notebook_utils import math_eq, math_eq_editor, spec_md

    pdealchemy_error = PDEAlchemyError
    return (
        build_notebook_report,
        build_report_chart_views,
        build_report_table_views,
        compose_report_view,
        create_notebook_report_controls,
        math_eq,
        math_eq_editor,
        mo,
        pdealchemy_error,
        render_notebook_report_controls,
        selection_from_controls,
        spec_md,
    )


@app.cell
def title(mo):
    mo.md("""
    # Black-Scholes European Call — Specification + Outputs
    """)
    return


@app.cell
def abstract_intro(mo):
    mo.md("""
    ## Abstract / Intro
    This notebook specifies a standard European vanilla call under Black-Scholes dynamics,
    then produces configurable pricing and sensitivities outputs in table and chart form.
    """)
    return


@app.cell
def assumptions(mo):
    mo.md("""
    ## Assumptions
    - Pricing is under the risk-neutral measure.
    - The market is complete for the specified factor structure.
    - Dynamics are diffusion-only (no jump terms).
    - Terminal and boundary conditions are well defined for a unique solution.
    - Constant risk-free rate and constant volatility (Black-Scholes baseline).
    """)
    return


@app.cell
def instrument(mo):
    mo.md("""
    European Call
    """)
    return


@app.cell
def numeraire(math_eq):
    math_eq("library/numeraire/domestic_aud.md")
    return


@app.cell
def sde(math_eq):
    math_eq("library/sde/black_scholes_geometric_brownian_motion.md", name="Risk-neutral SDE")
    return


@app.cell
def pde(math_eq_editor):
    math_eq_editor("library/pde/black_scholes.md", name="Main PDE operator")
    return


@app.cell
def payoff(math_eq):
    math_eq("library/payoff/vanilla_call.md")
    return


@app.cell
def boundary_lower(math_eq):
    math_eq("library/boundary/dirichlet_s0.md")
    return


@app.cell
def boundary_upper(math_eq):
    math_eq("library/boundary/asymptotic_call.md")
    return


@app.cell
def discretisation(spec_md):
    spec_md("library/discretisation/crank_nicolson_standard.md")
    return


@app.cell
def data_rates(math_eq):
    math_eq("library/data/rates_flat.md")
    return


@app.cell
def data_volatility(math_eq):
    math_eq("library/data/volatility_constant.md")
    return


@app.cell
def references(mo):
    mo.md("""
    ## References
    - Black, F. & Scholes, M. (1973). *The Pricing of Options and Corporate Liabilities*.
    - Merton, R. C. (1973). *Theory of Rational Option Pricing*.
    """)
    return


@app.cell
def output_controls(
    create_notebook_report_controls,
    mo,
    render_notebook_report_controls,
):
    controls = create_notebook_report_controls(
        mo,
        runtime_toml_default="examples/notebooks/black_scholes_pricing.toml",
        equation_library_default="library",
    )
    render_notebook_report_controls(
        mo,
        controls,
        title="## Reporting outputs",
        description=(
            "Use these controls after generating runtime TOML to select report sections, "
            "and show tables and/or Plotly charts."
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
def _(build_report_table_views, mo, report, selection):
    table_views = build_report_table_views(
        mo,
        report=report,
        selection=selection,
    )
    return (table_views,)


@app.cell
def _(build_report_chart_views, report, selection):
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
