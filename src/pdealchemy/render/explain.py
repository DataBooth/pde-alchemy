"""Explain renderer for validated pricing configurations."""

from __future__ import annotations

import sympy as sp

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import RenderError
from pdealchemy.math_bridge.problem import SymbolicPricingProblem

_SUPPORTED_OUTPUT_FORMATS = {"text", "markdown", "latex"}


def _text_expression(expression: sp.Expr) -> str:
    return str(expression)


def _latex_expression(expression: sp.Expr) -> str:
    return sp.latex(expression)


def _format_parameters(config_data: PricingConfig) -> str:
    if not config_data.process.parameters:
        return "(none)"
    return ", ".join(
        f"{name}={value:g}" for name, value in sorted(config_data.process.parameters.items())
    )


def _feature_lines(config_data: PricingConfig) -> tuple[str, str, str]:
    """Return text, markdown, and latex feature summaries."""
    if config_data.features is None:
        return "(none)", "(none)", "(none)"

    lines_text: list[str] = []
    lines_markdown: list[str] = []
    lines_latex: list[str] = []

    if config_data.features.barrier is not None:
        barrier = config_data.features.barrier
        text_line = f"Barrier {barrier.type} at level {barrier.level:g}, rebate {barrier.rebate:g}"
        lines_text.append(text_line)
        lines_markdown.append(f"- `{text_line}`")
        lines_latex.append(
            f"\\text{{Barrier: {barrier.type}, level={barrier.level:g}, rebate={barrier.rebate:g}}}"
        )

    if config_data.features.asian is not None:
        asian = config_data.features.asian
        observations = ", ".join(f"{value:g}" for value in asian.observation_times)
        text_line = f"Asian {asian.averaging} observations at [{observations}]"
        lines_text.append(text_line)
        lines_markdown.append(f"- `{text_line}`")
        lines_latex.append(
            f"\\text{{Asian: {asian.averaging}, observation\\ times=[{observations}]}}"
        )

    if config_data.features.dividends is not None:
        events = config_data.features.dividends.events
        if events:
            rendered_events = ", ".join(
                f"(t={event.time:g}, amount={event.amount:g})" for event in events
            )
            text_line = f"Discrete dividends {rendered_events}"
        else:
            text_line = "Discrete dividends (none)"
        lines_text.append(text_line)
        lines_markdown.append(f"- `{text_line}`")
        lines_latex.append(f"\\text{{{text_line}}}")

    if not lines_text:
        return "(none)", "(none)", "(none)"

    return "\n".join(lines_text), "\n".join(lines_markdown), " \\\\ ".join(lines_latex)


def _build_text_pde(symbolic_problem: SymbolicPricingProblem) -> str:
    transport_terms = [
        f"({_text_expression(symbolic_problem.drift[variable].sympy_expression)}) * ∂V/∂{variable}"
        for variable in symbolic_problem.state_variables
    ]
    diffusion_terms = [
        f"0.5 * ({_text_expression(symbolic_problem.diffusion[variable].sympy_expression)})^2 "
        f"* ∂²V/∂{variable}²"
        for variable in symbolic_problem.state_variables
    ]
    discount_symbol = "r" if "r" in symbolic_problem.parameter_values else "discount_rate"
    joined_terms = " + ".join(transport_terms + diffusion_terms + [f"- {discount_symbol} * V"])
    return f"∂V/∂t + {joined_terms} = 0"


def _build_latex_pde(symbolic_problem: SymbolicPricingProblem) -> str:
    transport_terms = [
        (
            f"\\left({_latex_expression(symbolic_problem.drift[variable].sympy_expression)}\\right)"
            f"\\frac{{\\partial V}}{{\\partial {variable}}}"
        )
        for variable in symbolic_problem.state_variables
    ]
    diffusion_terms = [
        (
            "\\frac{1}{2}"
            f"\\left({_latex_expression(symbolic_problem.diffusion[variable].sympy_expression)}\\right)^2"
            f"\\frac{{\\partial^2 V}}{{\\partial {variable}^2}}"
        )
        for variable in symbolic_problem.state_variables
    ]
    discount_symbol = "r" if "r" in symbolic_problem.parameter_values else "r_d"
    joined_terms = " + ".join(transport_terms + diffusion_terms + [f"- {discount_symbol}V"])
    return f"\\frac{{\\partial V}}{{\\partial t}} + {joined_terms} = 0"


def _text_sde_line(symbolic_problem: SymbolicPricingProblem, variable: str) -> str:
    drift_expression = _text_expression(symbolic_problem.drift[variable].sympy_expression)
    diffusion_expression = _text_expression(symbolic_problem.diffusion[variable].sympy_expression)
    return f"d{variable} = ({drift_expression}) dt + ({diffusion_expression}) dW_{variable}"


def _markdown_sde_line(symbolic_problem: SymbolicPricingProblem, variable: str) -> str:
    return f"- `{_text_sde_line(symbolic_problem, variable)}`"


def _latex_sde_line(symbolic_problem: SymbolicPricingProblem, variable: str) -> str:
    drift_expression = _latex_expression(symbolic_problem.drift[variable].sympy_expression)
    diffusion_expression = _latex_expression(symbolic_problem.diffusion[variable].sympy_expression)
    return (
        f"d{variable} = "
        f"\\left({drift_expression}\\right)dt + "
        f"\\left({diffusion_expression}\\right)dW_{{{variable}}}"
    )


def _text_grid_line(config_data: PricingConfig, variable: str) -> str:
    lower_bound = config_data.numerics.grid.lower[variable]
    upper_bound = config_data.numerics.grid.upper[variable]
    points = config_data.numerics.grid.points[variable]
    return f"- {variable}: [{lower_bound}, {upper_bound}], {points} points"


def _markdown_grid_line(config_data: PricingConfig, variable: str) -> str:
    lower_bound = config_data.numerics.grid.lower[variable]
    upper_bound = config_data.numerics.grid.upper[variable]
    points = config_data.numerics.grid.points[variable]
    return f"- `{variable}` in [`{lower_bound}`, `{upper_bound}`], `{points}` points"


def _latex_grid_line(config_data: PricingConfig, variable: str) -> str:
    lower_bound = config_data.numerics.grid.lower[variable]
    upper_bound = config_data.numerics.grid.upper[variable]
    points = config_data.numerics.grid.points[variable]
    return f"{variable} \\in [{lower_bound}, {upper_bound}], {points}\\text{{ points}}"


def _render_text(config_data: PricingConfig, symbolic_problem: SymbolicPricingProblem) -> str:
    state_variables = ", ".join(symbolic_problem.state_variables)
    features_text, _, _ = _feature_lines(config_data)
    sde_lines = "\n".join(
        _text_sde_line(symbolic_problem, variable) for variable in symbolic_problem.state_variables
    )
    grid_lines = "\n".join(
        _text_grid_line(config_data, variable) for variable in symbolic_problem.state_variables
    )

    return (
        "PDEAlchemy Explain\n"
        "-----------------\n"
        f"Instrument: {config_data.instrument.kind} ({config_data.instrument.exercise})\n"
        f"Maturity: {config_data.instrument.maturity}\n"
        f"State variables: {state_variables}\n"
        f"Parameters: {_format_parameters(config_data)}\n\n"
        "Stochastic model (SDE)\n"
        f"{sde_lines}\n\n"
        "Pricing PDE\n"
        f"{_build_text_pde(symbolic_problem)}\n\n"
        "Terminal condition\n"
        f"V(T, state) = {_text_expression(symbolic_problem.payoff.sympy_expression)}\n\n"
        "Discrete / exotic features\n"
        f"{features_text}\n\n"
        "Numerical setup\n"
        f"Backend: {config_data.numerics.backend}\n"
        f"Scheme: {config_data.numerics.scheme}\n"
        f"Time steps: {config_data.numerics.time_steps}\n"
        f"Grid:\n{grid_lines}"
    )


def _render_markdown(config_data: PricingConfig, symbolic_problem: SymbolicPricingProblem) -> str:
    state_variables = ", ".join(symbolic_problem.state_variables)
    _, features_markdown, _ = _feature_lines(config_data)
    drift_summary = "; ".join(
        (f"{variable}: {_text_expression(symbolic_problem.drift[variable].sympy_expression)}")
        for variable in symbolic_problem.state_variables
    )
    diffusion_summary = "; ".join(
        (f"{variable}: {_text_expression(symbolic_problem.diffusion[variable].sympy_expression)}")
        for variable in symbolic_problem.state_variables
    )
    sde_lines = "\n".join(
        _markdown_sde_line(symbolic_problem, variable)
        for variable in symbolic_problem.state_variables
    )
    grid_lines = "\n".join(
        _markdown_grid_line(config_data, variable) for variable in symbolic_problem.state_variables
    )

    return (
        "# PDEAlchemy Explain\n"
        "## Instrument\n"
        f"- Kind: `{config_data.instrument.kind}`\n"
        f"- Exercise: `{config_data.instrument.exercise}`\n"
        f"- Maturity: `{config_data.instrument.maturity}`\n"
        f"- State variables: `{state_variables}`\n"
        f"- Parameters: `{_format_parameters(config_data)}`\n"
        f"- Drift: `{drift_summary}`\n"
        f"- Diffusion: `{diffusion_summary}`\n"
        "## Stochastic model (SDE)\n"
        f"{sde_lines}\n"
        "## Pricing PDE\n"
        f"`{_build_text_pde(symbolic_problem)}`\n"
        "## Terminal condition\n"
        f"`V(T, state) = {_text_expression(symbolic_problem.payoff.sympy_expression)}`\n"
        "## Discrete / exotic features\n"
        f"{features_markdown}\n"
        "## Numerical setup\n"
        f"- Backend: `{config_data.numerics.backend}`\n"
        f"- Scheme: `{config_data.numerics.scheme}`\n"
        f"- Time steps: `{config_data.numerics.time_steps}`\n"
        "- Grid:\n"
        f"{grid_lines}"
    )


def _render_latex(config_data: PricingConfig, symbolic_problem: SymbolicPricingProblem) -> str:
    _, _, features_latex = _feature_lines(config_data)
    sde_lines = "\n".join(
        _latex_sde_line(symbolic_problem, variable) for variable in symbolic_problem.state_variables
    )
    payoff_latex = _latex_expression(symbolic_problem.payoff.sympy_expression)
    state_variables = ", ".join(symbolic_problem.state_variables)

    grid_lines = " \\\\ ".join(
        _latex_grid_line(config_data, variable) for variable in symbolic_problem.state_variables
    )

    return (
        "\\section*{PDEAlchemy Explain}\n"
        f"\\textbf{{Instrument}}: {config_data.instrument.kind}"
        f"\\ ({config_data.instrument.exercise})\\\\\n"
        f"\\textbf{{Maturity}}: {config_data.instrument.maturity}\\\\\n"
        f"\\textbf{{State variables}}: {state_variables}\\\\\n"
        f"\\textbf{{Parameters}}: {_format_parameters(config_data)}\n\n"
        "\\subsection*{Stochastic model}\n"
        "\\[\n"
        f"{sde_lines}\n"
        "\\]\n\n"
        "\\subsection*{Pricing PDE}\n"
        "\\[\n"
        f"{_build_latex_pde(symbolic_problem)}\n"
        "\\]\n\n"
        "\\subsection*{Terminal condition}\n"
        "\\[\n"
        f"V(T, state) = {payoff_latex}\n"
        "\\]\n\n"
        "\\subsection*{Discrete / exotic features}\n"
        f"{features_latex}\n\n"
        "\\subsection*{Numerical setup}\n"
        f"\\textbf{{Backend}}: {config_data.numerics.backend}\\\\\n"
        f"\\textbf{{Scheme}}: {config_data.numerics.scheme}\\\\\n"
        f"\\textbf{{Time steps}}: {config_data.numerics.time_steps}\\\\\n"
        f"\\textbf{{Grid}}: {grid_lines}"
    )


def render_explain_output(
    config_data: PricingConfig,
    symbolic_problem: SymbolicPricingProblem,
    *,
    output_format: str,
) -> str:
    """Render explain output in the selected format."""
    if output_format not in _SUPPORTED_OUTPUT_FORMATS:
        raise RenderError(
            "Unsupported explain output format.",
            details=output_format,
            suggestion="Use one of: text, markdown, latex.",
        )

    if output_format == "text":
        return _render_text(config_data, symbolic_problem)
    if output_format == "markdown":
        return _render_markdown(config_data, symbolic_problem)
    return _render_latex(config_data, symbolic_problem)
