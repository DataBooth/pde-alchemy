"""Symbolic expression parsing and numeric compilation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from pdealchemy.exceptions import MathBridgeError

_ALLOWED_FUNCTIONS: dict[str, Any] = {
    "abs": sp.Abs,
    "exp": sp.exp,
    "log": sp.log,
    "max": sp.Max,
    "min": sp.Min,
    "sqrt": sp.sqrt,
}


@dataclass(frozen=True)
class ParsedExpression:
    """Parsed symbolic expression with tracked free symbols."""

    raw_expression: str
    sympy_expression: sp.Expr
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class CompiledExpression:
    """Numerically evaluable expression callable."""

    symbol_order: tuple[str, ...]
    evaluator: Any

    def __call__(self, *args: Any) -> Any:
        """Evaluate the compiled expression using positional arguments."""
        if len(args) != len(self.symbol_order):
            raise MathBridgeError(
                "Compiled expression called with incorrect number of arguments.",
                details=(
                    f"Expected {len(self.symbol_order)} values for "
                    f"symbols {self.symbol_order}, got {len(args)}."
                ),
            )
        return self.evaluator(*args)


def _validate_functions(expression: sp.Expr) -> None:
    """Reject unsupported function calls in expressions."""
    unsupported = sorted(
        {
            function_call.func.__name__
            for function_call in expression.atoms(sp.Function)
            if function_call.func.__name__ not in {"Abs", "Max", "Min", "exp", "log", "sqrt"}
        }
    )
    if unsupported:
        raise MathBridgeError(
            "Expression uses unsupported function(s).",
            details=", ".join(unsupported),
            suggestion="Use only abs, max, min, exp, log, or sqrt for now.",
        )


def parse_expression(
    expression: str,
    *,
    allowed_symbols: set[str],
) -> ParsedExpression:
    """Parse expression into SymPy while enforcing symbol safety."""
    if not expression.strip():
        raise MathBridgeError("Expression must not be empty.")

    symbol_locals = {name: sp.Symbol(name) for name in allowed_symbols}
    locals_dict = {**symbol_locals, **_ALLOWED_FUNCTIONS}

    try:
        parsed_expression = sp.sympify(expression, locals=locals_dict, evaluate=False)
    except (sp.SympifyError, TypeError) as exc:
        raise MathBridgeError(
            "Failed to parse symbolic expression.",
            details=str(exc),
            suggestion="Check expression syntax and supported functions.",
        ) from exc

    _validate_functions(parsed_expression)

    unknown_symbols = sorted(
        symbol_name
        for symbol_name in (str(symbol) for symbol in parsed_expression.free_symbols)
        if symbol_name not in allowed_symbols
    )
    if unknown_symbols:
        raise MathBridgeError(
            "Expression references unknown symbols.",
            details=", ".join(unknown_symbols),
            suggestion="Declare symbols in process.state_variables or process.parameters.",
        )

    symbols = tuple(sorted(str(symbol) for symbol in parsed_expression.free_symbols))
    return ParsedExpression(
        raw_expression=expression,
        sympy_expression=parsed_expression,
        symbols=symbols,
    )


def compile_expression(
    parsed_expression: ParsedExpression,
    *,
    substitutions: dict[str, float] | None = None,
) -> CompiledExpression:
    """Compile a parsed expression into a NumPy-callable function."""
    substitutions = substitutions or {}
    relevant_substitutions = {
        symbol_name: value
        for symbol_name, value in substitutions.items()
        if symbol_name in parsed_expression.symbols
    }

    substituted_expression = parsed_expression.sympy_expression.subs(relevant_substitutions)
    remaining_symbols = tuple(
        symbol_name
        for symbol_name in parsed_expression.symbols
        if symbol_name not in relevant_substitutions
    )
    ordered_symbols = [sp.Symbol(name) for name in remaining_symbols]
    evaluator = sp.lambdify(ordered_symbols, substituted_expression, modules=["numpy"])

    return CompiledExpression(symbol_order=remaining_symbols, evaluator=evaluator)
