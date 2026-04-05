"""Analytical benchmark utilities."""

from __future__ import annotations

import math
from statistics import NormalDist

from pdealchemy.exceptions import ValidationError

_NORMAL_DIST = NormalDist()


def _normal_cdf(value: float) -> float:
    return _NORMAL_DIST.cdf(value)


def black_scholes_price(
    *,
    spot: float,
    strike: float,
    maturity: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    option_style: str,
) -> float:
    """Compute Black-Scholes analytical price for vanilla options."""
    if spot <= 0.0 or strike <= 0.0:
        raise ValidationError("Spot and strike must be positive for Black-Scholes benchmark.")
    if maturity <= 0.0:
        raise ValidationError("Maturity must be positive for Black-Scholes benchmark.")
    if volatility <= 0.0:
        raise ValidationError("Volatility must be positive for Black-Scholes benchmark.")

    sqrt_maturity = math.sqrt(maturity)
    volatility_term = volatility * sqrt_maturity
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility) * maturity
    ) / volatility_term
    d2 = d1 - volatility_term

    discounted_spot = spot * math.exp(-dividend_yield * maturity)
    discounted_strike = strike * math.exp(-risk_free_rate * maturity)

    style_normalised = option_style.lower()
    if style_normalised == "call":
        return discounted_spot * _normal_cdf(d1) - discounted_strike * _normal_cdf(d2)
    if style_normalised == "put":
        return discounted_strike * _normal_cdf(-d2) - discounted_spot * _normal_cdf(-d1)

    raise ValidationError(
        "Unsupported option style for analytical Black-Scholes benchmark.",
        details=option_style,
        suggestion="Use 'call' or 'put'.",
    )
