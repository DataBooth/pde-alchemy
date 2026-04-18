"""Vanilla QuantLib pricing route internals."""

from __future__ import annotations

import QuantLib

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.adapters.quantlib_market import (
    _build_volatility_handle,
    _build_yield_curve_handle,
    _market_inputs,
    _option_type,
    _rate_curve_kind,
    _resolve_scheme,
    _volatility_structure_kind,
)
from pdealchemy.core.models import PricingResult


def _price_vanilla_fd(config_data: PricingConfig, *, style: str) -> PricingResult:
    """Price a 1D vanilla European option with QuantLib FD engine."""
    spot, strike, risk_free_rate, volatility, dividend_yield = _market_inputs(config_data)
    option_type = _option_type(style)
    maturity_years = config_data.instrument.maturity
    maturity_days = max(1, int(round(maturity_years * 365)))
    scheme = _resolve_scheme(config_data.numerics.scheme)

    calendar = QuantLib.NullCalendar()
    day_count = QuantLib.Actual365Fixed()
    evaluation_date = QuantLib.Date.todaysDate()
    QuantLib.Settings.instance().evaluationDate = evaluation_date

    maturity_date = evaluation_date + maturity_days
    payoff = QuantLib.PlainVanillaPayoff(option_type, strike)
    exercise = QuantLib.EuropeanExercise(maturity_date)
    option = QuantLib.VanillaOption(payoff, exercise)

    spot_handle = QuantLib.QuoteHandle(QuantLib.SimpleQuote(spot))
    market = config_data.market
    dividend_curve = _build_yield_curve_handle(
        None if market is None else market.dividend_curve,
        fallback_rate=dividend_yield,
        evaluation_date=evaluation_date,
        day_count=day_count,
    )
    risk_free_curve = _build_yield_curve_handle(
        None if market is None else market.risk_free_curve,
        fallback_rate=risk_free_rate,
        evaluation_date=evaluation_date,
        day_count=day_count,
    )
    volatility_curve = _build_volatility_handle(
        None if market is None else market.volatility,
        fallback_volatility=volatility,
        evaluation_date=evaluation_date,
        calendar=calendar,
        day_count=day_count,
    )

    process = QuantLib.BlackScholesMertonProcess(
        spot_handle,
        dividend_curve,
        risk_free_curve,
        volatility_curve,
    )

    time_steps = config_data.numerics.time_steps
    space_steps = config_data.numerics.grid.points["S"]
    damping_steps = config_data.numerics.damping_steps
    engine = QuantLib.FdBlackScholesVanillaEngine(
        process,
        time_steps,
        space_steps,
        damping_steps,
        scheme,
    )
    option.setPricingEngine(engine)
    price = float(option.NPV())

    return PricingResult(
        price=price,
        backend="quantlib",
        engine="FdBlackScholesVanillaEngine",
        metadata={
            "time_steps": time_steps,
            "space_steps": space_steps,
            "scheme": config_data.numerics.scheme,
            "maturity_years": maturity_years,
            "rate_curve": _rate_curve_kind(config_data),
            "volatility_structure": _volatility_structure_kind(config_data),
        },
    )
