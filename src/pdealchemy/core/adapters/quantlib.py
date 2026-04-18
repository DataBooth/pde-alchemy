"""QuantLib finite-difference adapter and Monte Carlo exotic route façade."""

from __future__ import annotations

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.adapters.quantlib_exotic import _price_exotic_monte_carlo
from pdealchemy.core.adapters.quantlib_market import (
    _has_exotic_features,
    _require_option_style,
)
from pdealchemy.core.adapters.quantlib_vanilla import _price_vanilla_fd
from pdealchemy.core.models import PricingResult
from pdealchemy.exceptions import PricingError


def price_with_quantlib(config_data: PricingConfig) -> PricingResult:
    """Price a 1D option using QuantLib-backed routes."""
    if tuple(config_data.process.state_variables) != ("S",):
        raise PricingError(
            "Current QuantLib adapter supports one state variable named 'S'.",
            suggestion="Use a 1D config now; multi-dimensional adapters are planned next.",
        )
    if config_data.instrument.exercise != "european":
        raise PricingError(
            "Current QuantLib adapter supports European exercise only.",
            suggestion="Set instrument.exercise to 'european'.",
        )
    if config_data.instrument.kind not in {
        "vanilla_option",
        "generic_option",
        "exotic_option",
    }:
        raise PricingError(
            "Unsupported instrument.kind for current QuantLib adapter.",
            details=config_data.instrument.kind,
            suggestion="Use vanilla_option, generic_option, or exotic_option.",
        )

    style = _require_option_style(config_data.instrument.style)
    if _has_exotic_features(config_data):
        return _price_exotic_monte_carlo(config_data, style=style)
    return _price_vanilla_fd(config_data, style=style)
