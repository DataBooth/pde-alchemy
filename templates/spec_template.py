import marimo

app = marimo.App()


@app.cell
def notebook_context():
    import marimo as mo

    from pdealchemy.notebook_utils import math_eq, spec_md

    return math_eq, mo, spec_md


@app.cell
def title(mo):
    mo.md("# {{Instrument Name}} — Specification Notebook")
    return


@app.cell
def abstract_intro(mo):
    mo.md(
        """
        ## Abstract / Intro
        {{Short overview of the instrument specification and intended usage.}}
        """
    )
    return


@app.cell
def assumptions(mo):
    mo.md(
        """
        ## Assumptions
        - Pricing is under the risk-neutral measure.
        - Markets are complete for the specified factors and claims.
        - Dynamics are diffusion-only (no jump terms).
        - Terminal and boundary conditions are well defined for a unique solution.
        """
    )
    return


@app.cell
def instrument(mo):
    """{{Short description of the instrument}}."""
    mo.md("{{Instrument Type}}")
    return


@app.cell
def numeraire(math_eq):
    """{{Numeraire description}}."""
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
    math_eq("library/pde/{{pde_file}}.md", name="Main PDE operator")
    return


@app.cell
def payoff(math_eq):
    """Terminal condition."""
    math_eq("library/payoff/{{payoff_file}}.md")
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
    mo.md(
        """
        ## References
        - {{Primary reference 1}}
        - {{Primary reference 2}}
        """
    )
    return


if __name__ == "__main__":
    app.run()
