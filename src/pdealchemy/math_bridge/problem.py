"""Bridge typed pricing configs into parsed symbolic expression objects."""

from __future__ import annotations

from dataclasses import dataclass

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import MathBridgeError
from pdealchemy.math_bridge.parser import ParsedExpression, parse_expression


@dataclass(frozen=True)
class SymbolicPricingProblem:
    """Parsed symbolic expressions extracted from pricing config."""

    state_variables: tuple[str, ...]
    parameter_values: dict[str, float]
    payoff: ParsedExpression
    drift: dict[str, ParsedExpression]
    diffusion: dict[str, ParsedExpression]


def _parse_with_context(
    expression: str,
    *,
    context_label: str,
    allowed_symbols: set[str],
) -> ParsedExpression:
    """Parse expression and wrap errors with context."""
    try:
        return parse_expression(expression, allowed_symbols=allowed_symbols)
    except MathBridgeError as exc:
        details = exc.message if exc.details is None else f"{exc.message}: {exc.details}"
        raise MathBridgeError(
            f"Failed to parse {context_label}.",
            details=details,
            suggestion=exc.suggestion,
        ) from exc


def build_symbolic_problem(config_data: PricingConfig) -> SymbolicPricingProblem:
    """Build parsed symbolic expressions from validated configuration."""
    state_variables = tuple(config_data.process.state_variables)
    parameter_values = dict(config_data.process.parameters)
    allowed_symbols = set(state_variables) | set(parameter_values)

    payoff = _parse_with_context(
        config_data.instrument.payoff,
        context_label="instrument.payoff",
        allowed_symbols=allowed_symbols,
    )
    drift = {
        variable: _parse_with_context(
            expression,
            context_label=f"process.drift.{variable}",
            allowed_symbols=allowed_symbols,
        )
        for variable, expression in config_data.process.drift.items()
    }
    diffusion = {
        variable: _parse_with_context(
            expression,
            context_label=f"process.diffusion.{variable}",
            allowed_symbols=allowed_symbols,
        )
        for variable, expression in config_data.process.diffusion.items()
    }

    return SymbolicPricingProblem(
        state_variables=state_variables,
        parameter_values=parameter_values,
        payoff=payoff,
        drift=drift,
        diffusion=diffusion,
    )
