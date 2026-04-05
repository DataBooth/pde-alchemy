import marimo

__generated_with = "0.22.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

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
        value="Vanilla European call",
        label="Example configuration",
    )
    run_analytical = mo.ui.checkbox(
        value=False,
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
            mo.md("## PDEAlchemy marimo explorer"),
            example,
            run_analytical,
            tolerance,
            monte_carlo_paths,
        ]
    )
    return example, monte_carlo_paths, run_analytical, tolerance


@app.cell
def _(
    PDEAlchemyError,
    Path,
    canonical_example_paths,
    example,
    load_canonical_example,
    mo,
    monte_carlo_paths,
    prepare_notebook_outputs,
    repository_root_from_notebook,
    run_analytical,
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
        outputs = prepare_notebook_outputs(
            config_data,
            run_analytical=run_analytical.value,
            tolerance=tolerance.value,
        )
        pricing_result = outputs.pricing_result

        analytical_summary = "not run"
        if outputs.analytical_outcome is not None:
            outcome = outputs.analytical_outcome
            analytical_summary = (
                f"{'passed' if outcome.passed else 'failed'} "
                f"(abs error {outcome.absolute_error:.8f}, "
                f"tolerance {outcome.tolerance:.8f})"
            )
        view = mo.vstack(
            [
                mo.md(
                    "### Canonical config paths\n"
                    f"{path_summary}\n\n"
                    "### Pricing result\n"
                    f"- backend: `{pricing_result.backend}`\n"
                    f"- engine: `{pricing_result.engine}`\n"
                    f"- value: `{pricing_result.price:.8f}`\n"
                    f"- analytical benchmark: `{analytical_summary}`\n"
                ),
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
