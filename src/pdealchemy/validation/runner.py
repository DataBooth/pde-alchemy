"""Validation runner for progressive benchmark checks."""

from __future__ import annotations

from dataclasses import dataclass

from pdealchemy.config.models import PricingConfig
from pdealchemy.core import price_config
from pdealchemy.exceptions import ValidationError
from pdealchemy.validation.analytical import black_scholes_price


@dataclass(frozen=True)
class ValidationOutcome:
    """Result of a single validation benchmark check."""

    name: str
    passed: bool
    model_price: float
    benchmark_price: float
    absolute_error: float
    tolerance: float


class ValidationRunner:
    """Run validation checks at different pyramid layers."""

    def run_analytical_black_scholes(
        self,
        config_data: PricingConfig,
        *,
        tolerance: float = 0.5,
    ) -> ValidationOutcome:
        """Compare model price with Black-Scholes closed-form benchmark."""
        if config_data.features is not None and (
            config_data.features.asian is not None
            or config_data.features.barrier is not None
            or (
                config_data.features.dividends is not None
                and bool(config_data.features.dividends.events)
            )
        ):
            raise ValidationError(
                "Analytical Black-Scholes benchmark is only available for non-exotic configs."
            )
        if tuple(config_data.process.state_variables) != ("S",):
            raise ValidationError(
                "Analytical Black-Scholes benchmark currently supports 1D state variable S only."
            )
        if config_data.instrument.exercise != "european":
            raise ValidationError(
                "Analytical Black-Scholes benchmark currently supports European exercise only."
            )

        style = config_data.instrument.style
        if style is None:
            raise ValidationError(
                "Analytical Black-Scholes benchmark requires instrument.style.",
                suggestion="Use 'call' or 'put'.",
            )

        parameters = config_data.process.parameters
        spot = parameters.get("S0", parameters.get("spot"))
        strike = parameters.get("K", parameters.get("strike"))
        if spot is None or strike is None:
            raise ValidationError(
                "Analytical benchmark requires S0 (or spot) and K (or strike)."
            )
        if "r" not in parameters or "sigma" not in parameters:
            raise ValidationError(
                "Analytical benchmark requires r and sigma in process.parameters."
            )

        model_result = price_config(config_data)
        benchmark_price = black_scholes_price(
            spot=spot,
            strike=strike,
            maturity=config_data.instrument.maturity,
            risk_free_rate=parameters["r"],
            volatility=parameters["sigma"],
            dividend_yield=parameters.get("q", 0.0),
            option_style=style,
        )
        absolute_error = abs(model_result.price - benchmark_price)

        return ValidationOutcome(
            name="analytical_black_scholes",
            passed=absolute_error <= tolerance,
            model_price=model_result.price,
            benchmark_price=benchmark_price,
            absolute_error=absolute_error,
            tolerance=tolerance,
        )
