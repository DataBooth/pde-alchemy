import marimo

__generated_with = "0.22.4"
app = marimo.App()


@app.cell
def notebook_context():
    import marimo as mo

    from pdealchemy.notebook_utils import math_eq, spec_md

    return math_eq, mo, spec_md


@app.cell
def title(mo):
    mo.md("""
    # Black-Scholes European Call — Specification
    """)
    return


@app.cell
def abstract_intro(mo):
    mo.md("""
    ## Abstract / Intro
    This notebook specifies a standard European vanilla call under Black-Scholes dynamics.
    It is intended as the baseline specification before adding richer market structures and
    path-dependent features.
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
    """European vanilla call option in AUD."""
    mo.md("European Call")
    return


@app.cell
def numeraire(math_eq):
    """Domestic bank account numeraire in AUD."""
    math_eq("library/numeraire/domestic_aud.md")
    return


@app.cell
def sde(math_eq):
    """Risk-neutral asset dynamics."""
    math_eq("library/sde/black_scholes_geometric_brownian_motion.md", name="Risk-neutral SDE")
    return


@app.cell
def pde(math_eq):
    """Main PDE operator."""
    math_eq("library/pde/black_scholes.md", name="Main PDE operator")
    return


@app.cell
def payoff(math_eq):
    """Terminal condition."""
    math_eq("library/payoff/vanilla_call.md")
    return


@app.cell
def boundary_lower(math_eq):
    """Lower boundary."""
    math_eq("library/boundary/dirichlet_s0.md")
    return


@app.cell
def boundary_upper(math_eq):
    """Upper boundary."""
    math_eq("library/boundary/asymptotic_call.md")
    return


@app.cell
def discretisation(spec_md):
    """Numerical discretisation settings."""
    spec_md("library/discretisation/crank_nicolson_standard.md")
    return


@app.cell
def data_rates(math_eq):
    """Risk-free rates source."""
    math_eq("library/data/rates_flat.md")
    return


@app.cell
def data_volatility(math_eq):
    """Volatility source."""
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


if __name__ == "__main__":
    app.run()
