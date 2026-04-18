"""Shared QuantLib adapter helpers for market inputs and common validations."""

from __future__ import annotations

import math
from collections.abc import Callable

import QuantLib

from pdealchemy.config.models import (
    ConstantVolatilityConfig,
    FlatRateCurveConfig,
    PricingConfig,
    SurfaceVolatilityConfig,
    TermVolatilityCurveConfig,
    ZeroRateCurveConfig,
)
from pdealchemy.exceptions import PricingError

_SCHEME_BUILDERS: dict[str, Callable[[], QuantLib.FdmSchemeDesc]] = {
    "crank_nicolson": QuantLib.FdmSchemeDesc.CrankNicolson,
    "douglas": QuantLib.FdmSchemeDesc.Douglas,
}


def _require_parameter(parameters: dict[str, float], name: str) -> float:
    if name not in parameters:
        raise PricingError(
            "Missing required model parameter for QuantLib pricing.",
            details=name,
            suggestion="Add it under process.parameters in your config.",
        )
    return parameters[name]


def _require_option_style(style: str | None) -> str:
    if style is None:
        raise PricingError(
            "QuantLib pricing requires instrument.style.",
            suggestion="Use 'call' or 'put'.",
        )

    style_normalised = style.lower()
    if style_normalised not in {"call", "put"}:
        raise PricingError(
            "Unsupported instrument.style for QuantLib adapter.",
            details=style,
            suggestion="Use 'call' or 'put'.",
        )
    return style_normalised


def _option_type(style: str) -> int:
    if style == "call":
        return QuantLib.Option.Call
    return QuantLib.Option.Put


def _resolve_scheme(scheme_name: str) -> QuantLib.FdmSchemeDesc:
    key = scheme_name.lower()
    if key not in _SCHEME_BUILDERS:
        supported = ", ".join(sorted(_SCHEME_BUILDERS))
        raise PricingError(
            "Unsupported finite-difference scheme for QuantLib adapter.",
            details=scheme_name,
            suggestion=f"Use one of: {supported}.",
        )
    return _SCHEME_BUILDERS[key]()


def _time_key(time_value: float) -> float:
    return round(time_value, 12)


def _has_exotic_features(config_data: PricingConfig) -> bool:
    features = config_data.features
    if features is None:
        return False
    has_dividends = features.dividends is not None and bool(features.dividends.events)
    return features.barrier is not None or features.asian is not None or has_dividends


def _year_fraction_to_days(year_fraction: float) -> int:
    return max(1, int(round(year_fraction * 365)))


def _term_structure_dates(
    evaluation_date: QuantLib.Date,
    times: list[float],
) -> list[QuantLib.Date]:
    dates: list[QuantLib.Date] = []
    previous_date = evaluation_date
    for time_value in times:
        candidate_date = evaluation_date + _year_fraction_to_days(time_value)
        if candidate_date <= previous_date:
            candidate_date = previous_date + 1
        dates.append(candidate_date)
        previous_date = candidate_date
    return dates


def _rate_curve_kind(config_data: PricingConfig) -> str:
    market = config_data.market
    if market is None or market.risk_free_curve is None:
        return "flat_parameter"
    return market.risk_free_curve.kind


def _volatility_structure_kind(config_data: PricingConfig) -> str:
    market = config_data.market
    if market is None or market.volatility is None:
        return "constant_parameter"
    return market.volatility.kind


def _resolve_flat_rate(
    *,
    curve_name: str,
    curve_config: FlatRateCurveConfig | ZeroRateCurveConfig | None,
    fallback_rate: float,
    require_flat: bool,
) -> float:
    if curve_config is None:
        return fallback_rate
    if isinstance(curve_config, FlatRateCurveConfig):
        return curve_config.rate
    if not require_flat:
        return fallback_rate
    raise PricingError(
        "Current exotic Monte Carlo route supports flat market curves only.",
        details=f"{curve_name}={curve_config.kind}",
        suggestion=(
            "Use a flat market curve for exotics now, or use process.parameters for r and q."
        ),
    )


def _resolve_constant_volatility(
    volatility_config: ConstantVolatilityConfig
    | TermVolatilityCurveConfig
    | SurfaceVolatilityConfig
    | None,
    *,
    fallback_volatility: float,
    require_flat: bool,
) -> float:
    if volatility_config is None:
        return fallback_volatility
    if isinstance(volatility_config, ConstantVolatilityConfig):
        return volatility_config.vol
    if not require_flat:
        return fallback_volatility
    raise PricingError(
        "Current exotic Monte Carlo route supports constant volatility only.",
        details=f"market.volatility={volatility_config.kind}",
        suggestion=(
            "Use market.volatility kind 'constant' for exotics now, "
            "or use process.parameters sigma."
        ),
    )


def _build_yield_curve_handle(
    curve_config: FlatRateCurveConfig | ZeroRateCurveConfig | None,
    *,
    fallback_rate: float,
    evaluation_date: QuantLib.Date,
    day_count: QuantLib.DayCounter,
) -> QuantLib.YieldTermStructureHandle:
    if curve_config is None:
        return QuantLib.YieldTermStructureHandle(
            QuantLib.FlatForward(evaluation_date, fallback_rate, day_count)
        )
    if isinstance(curve_config, FlatRateCurveConfig):
        return QuantLib.YieldTermStructureHandle(
            QuantLib.FlatForward(evaluation_date, curve_config.rate, day_count)
        )

    node_dates = _term_structure_dates(evaluation_date, curve_config.times)
    dates = [evaluation_date, *node_dates]
    rates = [curve_config.rates[0], *curve_config.rates]
    return QuantLib.YieldTermStructureHandle(QuantLib.ZeroCurve(dates, rates, day_count))


def _build_volatility_handle(
    volatility_config: ConstantVolatilityConfig
    | TermVolatilityCurveConfig
    | SurfaceVolatilityConfig
    | None,
    *,
    fallback_volatility: float,
    evaluation_date: QuantLib.Date,
    calendar: QuantLib.Calendar,
    day_count: QuantLib.DayCounter,
) -> QuantLib.BlackVolTermStructureHandle:
    if volatility_config is None:
        return QuantLib.BlackVolTermStructureHandle(
            QuantLib.BlackConstantVol(
                evaluation_date,
                calendar,
                fallback_volatility,
                day_count,
            )
        )
    if isinstance(volatility_config, ConstantVolatilityConfig):
        return QuantLib.BlackVolTermStructureHandle(
            QuantLib.BlackConstantVol(
                evaluation_date,
                calendar,
                volatility_config.vol,
                day_count,
            )
        )
    if isinstance(volatility_config, TermVolatilityCurveConfig):
        node_dates = _term_structure_dates(evaluation_date, volatility_config.times)
        return QuantLib.BlackVolTermStructureHandle(
            QuantLib.BlackVarianceCurve(
                evaluation_date,
                node_dates,
                volatility_config.vols,
                day_count,
            )
        )

    node_dates = _term_structure_dates(evaluation_date, volatility_config.times)
    volatility_matrix = QuantLib.Matrix(
        len(volatility_config.strikes),
        len(node_dates),
    )
    for column_index, row_values in enumerate(volatility_config.vols):
        for row_index, volatility in enumerate(row_values):
            volatility_matrix[row_index][column_index] = volatility

    return QuantLib.BlackVolTermStructureHandle(
        QuantLib.BlackVarianceSurface(
            evaluation_date,
            calendar,
            node_dates,
            volatility_config.strikes,
            volatility_matrix,
            day_count,
        )
    )


def _market_inputs(
    config_data: PricingConfig,
    *,
    require_flat_market_inputs: bool = False,
) -> tuple[float, float, float, float, float]:
    parameters = config_data.process.parameters

    spot = parameters.get("S0", parameters.get("spot"))
    if spot is None:
        raise PricingError(
            "Missing spot level for QuantLib pricing.",
            suggestion="Provide S0 (or spot) under process.parameters.",
        )

    strike = parameters.get("K", parameters.get("strike"))
    if strike is None:
        raise PricingError(
            "Missing strike for QuantLib pricing.",
            suggestion="Provide K (or strike) under process.parameters.",
        )

    risk_free_rate = _require_parameter(parameters, "r")
    volatility = _require_parameter(parameters, "sigma")
    dividend_yield = parameters.get("q", 0.0)

    if config_data.market is not None:
        risk_free_rate = _resolve_flat_rate(
            curve_name="market.risk_free_curve",
            curve_config=config_data.market.risk_free_curve,
            fallback_rate=risk_free_rate,
            require_flat=require_flat_market_inputs,
        )
        dividend_yield = _resolve_flat_rate(
            curve_name="market.dividend_curve",
            curve_config=config_data.market.dividend_curve,
            fallback_rate=dividend_yield,
            require_flat=require_flat_market_inputs,
        )
        volatility = _resolve_constant_volatility(
            config_data.market.volatility,
            fallback_volatility=volatility,
            require_flat=require_flat_market_inputs,
        )

    if not math.isfinite(volatility) or volatility <= 0.0:
        raise PricingError(
            "Invalid volatility parameter for QuantLib pricing.",
            details=str(volatility),
            suggestion="Set sigma to a positive finite value.",
        )
    if not math.isfinite(spot) or spot <= 0.0:
        raise PricingError(
            "Invalid spot parameter for QuantLib pricing.",
            details=str(spot),
            suggestion="Set S0 to a positive finite value.",
        )
    if not math.isfinite(strike) or strike <= 0.0:
        raise PricingError(
            "Invalid strike parameter for QuantLib pricing.",
            details=str(strike),
            suggestion="Set K to a positive finite value.",
        )

    return spot, strike, risk_free_rate, volatility, dividend_yield
