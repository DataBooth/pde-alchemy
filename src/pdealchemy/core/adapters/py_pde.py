"""py-pde adapter for vanilla Black-Scholes pricing."""

from __future__ import annotations

import math
from typing import cast

import numpy as np
import pde
from pde.solvers.base import ConvergenceError

from pdealchemy.config.models import (
    ConstantVolatilityConfig,
    FlatRateCurveConfig,
    PricingConfig,
    ZeroRateCurveConfig,
)
from pdealchemy.core.models import PricingResult
from pdealchemy.exceptions import PricingError


def _require_parameter(parameters: dict[str, float], name: str) -> float:
    if name not in parameters:
        raise PricingError(
            "Missing required model parameter for py_pde pricing.",
            details=name,
            suggestion="Add it under process.parameters in your config.",
        )
    return parameters[name]


def _require_option_style(style: str | None) -> str:
    if style is None:
        raise PricingError(
            "py_pde pricing requires instrument.style.",
            suggestion="Use 'call' or 'put'.",
        )

    style_normalised = style.lower()
    if style_normalised not in {"call", "put"}:
        raise PricingError(
            "Unsupported instrument.style for py_pde adapter.",
            details=style,
            suggestion="Use 'call' or 'put'.",
        )
    return style_normalised


def _resolve_flat_rate(
    *,
    curve_name: str,
    curve_config: FlatRateCurveConfig | ZeroRateCurveConfig | None,
    fallback_rate: float,
) -> float:
    if curve_config is None:
        return fallback_rate
    if isinstance(curve_config, FlatRateCurveConfig):
        return curve_config.rate
    raise PricingError(
        "py_pde backend currently supports flat market curves only.",
        details=f"{curve_name}={curve_config.kind}",
        suggestion="Use a flat market curve or process.parameters values for now.",
    )


def _resolve_constant_volatility(
    volatility_config: ConstantVolatilityConfig | None,
    *,
    fallback_volatility: float,
) -> float:
    if volatility_config is None:
        return fallback_volatility
    return volatility_config.vol


def _market_inputs(config_data: PricingConfig) -> tuple[float, float, float, float, float]:
    parameters = config_data.process.parameters

    spot = parameters.get("S0", parameters.get("spot"))
    if spot is None:
        raise PricingError(
            "Missing spot level for py_pde pricing.",
            suggestion="Provide S0 (or spot) under process.parameters.",
        )

    strike = parameters.get("K", parameters.get("strike"))
    if strike is None:
        raise PricingError(
            "Missing strike for py_pde pricing.",
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
        )
        dividend_yield = _resolve_flat_rate(
            curve_name="market.dividend_curve",
            curve_config=config_data.market.dividend_curve,
            fallback_rate=dividend_yield,
        )
        if config_data.market.volatility is not None and not isinstance(
            config_data.market.volatility,
            ConstantVolatilityConfig,
        ):
            raise PricingError(
                "py_pde backend currently supports constant market volatility only.",
                details=f"market.volatility={config_data.market.volatility.kind}",
                suggestion=(
                    "Use market.volatility kind 'constant' or process.parameters sigma for now."
                ),
            )
        volatility = _resolve_constant_volatility(
            config_data.market.volatility,
            fallback_volatility=volatility,
        )

    if not math.isfinite(volatility) or volatility <= 0.0:
        raise PricingError(
            "Invalid volatility parameter for py_pde pricing.",
            details=str(volatility),
            suggestion="Set sigma to a positive finite value.",
        )
    if not math.isfinite(spot) or spot <= 0.0:
        raise PricingError(
            "Invalid spot parameter for py_pde pricing.",
            details=str(spot),
            suggestion="Set S0 to a positive finite value.",
        )
    if not math.isfinite(strike) or strike <= 0.0:
        raise PricingError(
            "Invalid strike parameter for py_pde pricing.",
            details=str(strike),
            suggestion="Set K to a positive finite value.",
        )

    return spot, strike, risk_free_rate, volatility, dividend_yield


def _has_exotic_features(config_data: PricingConfig) -> bool:
    features = config_data.features
    if features is None:
        return False
    has_dividends = features.dividends is not None and bool(features.dividends.events)
    return features.barrier is not None or features.asian is not None or has_dividends


def _effective_spot_lower_bound(lower_bound: float, *, spot: float, strike: float) -> float:
    floor = max(min(spot, strike) * 1e-6, 1e-8)
    return max(lower_bound, floor)


def price_with_py_pde(config_data: PricingConfig) -> PricingResult:
    """Price a 1D vanilla European option using py-pde."""
    if tuple(config_data.process.state_variables) != ("S",):
        raise PricingError(
            "Current py_pde adapter supports one state variable named 'S'.",
            suggestion="Use a 1D config now; multi-dimensional adapters are planned next.",
        )
    if config_data.instrument.exercise != "european":
        raise PricingError(
            "Current py_pde adapter supports European exercise only.",
            suggestion="Set instrument.exercise to 'european'.",
        )
    if _has_exotic_features(config_data) or config_data.instrument.kind == "exotic_option":
        raise PricingError(
            "Current py_pde adapter supports vanilla routes only.",
            suggestion="Use quantlib backend for exotic feature combinations.",
        )
    if config_data.instrument.kind not in {"vanilla_option", "generic_option"}:
        raise PricingError(
            "Unsupported instrument.kind for current py_pde adapter.",
            details=config_data.instrument.kind,
            suggestion="Use vanilla_option or generic_option for now.",
        )

    style = _require_option_style(config_data.instrument.style)
    spot, strike, risk_free_rate, volatility, dividend_yield = _market_inputs(config_data)

    maturity_years = config_data.instrument.maturity
    time_steps = config_data.numerics.time_steps
    if time_steps <= 0:
        raise PricingError("py_pde backend requires numerics.time_steps > 0.")

    spot_lower_bound = config_data.numerics.grid.lower["S"]
    spot_upper_bound = config_data.numerics.grid.upper["S"]
    effective_lower_bound = _effective_spot_lower_bound(
        spot_lower_bound,
        spot=spot,
        strike=strike,
    )
    if spot_upper_bound <= effective_lower_bound:
        raise PricingError(
            "Invalid spatial bounds for py_pde pricing.",
            details=(
                f"lower={effective_lower_bound:.8g}, "
                f"upper={spot_upper_bound:.8g}"
            ),
            suggestion="Set numerics.grid.upper.S greater than numerics.grid.lower.S.",
        )

    log_lower_bound = math.log(effective_lower_bound / strike)
    log_upper_bound = math.log(spot_upper_bound / strike)
    if log_upper_bound <= log_lower_bound:
        raise PricingError("py_pde log-space domain bounds are invalid.")

    spot_log = math.log(spot / strike)
    if not (log_lower_bound <= spot_log <= log_upper_bound):
        raise PricingError(
            "Spot lies outside py_pde log-space grid bounds.",
            details=(
                f"log(spot/strike)={spot_log:.8g}, "
                f"bounds=({log_lower_bound:.8g}, {log_upper_bound:.8g})"
            ),
            suggestion="Adjust numerics.grid bounds for S.",
        )

    space_steps = config_data.numerics.grid.points["S"]
    grid = pde.CartesianGrid([(log_lower_bound, log_upper_bound)], space_steps)
    log_spots = grid.axes_coords[0]

    if style == "call":
        payoff_values = [max(strike * math.exp(log_spot) - strike, 0.0) for log_spot in log_spots]
        boundary_conditions: list[dict[str, float]] = [
            {"value": 0.0},
            {"derivative": strike * math.exp(log_upper_bound)},
        ]
    else:
        payoff_values = [max(strike - strike * math.exp(log_spot), 0.0) for log_spot in log_spots]
        boundary_conditions = [{"derivative": 0.0}, {"value": 0.0}]

    state = pde.ScalarField(grid, payoff_values)
    diffusion = 0.5 * volatility * volatility
    convection = risk_free_rate - dividend_yield - 0.5 * volatility * volatility
    equation = pde.PDE(
        {"V": "diffusion * d_dx(d_dx(V)) + convection * d_dx(V) - r * V"},
        bc=boundary_conditions,
        consts={
            "diffusion": diffusion,
            "convection": convection,
            "r": risk_free_rate,
        },
    )

    try:
        solved_state = equation.solve(
            state,
            t_range=maturity_years,
            dt=maturity_years / time_steps,
            tracker=None,
            backend="numpy",
            solver="crank-nicolson",
            maxiter=1_000,
            maxerror=1e-8,
        )
    except ConvergenceError as exc:
        raise PricingError(
            "py_pde solver did not converge.",
            details=str(exc),
            suggestion="Increase numerics.time_steps or adjust grid bounds.",
        ) from exc
    if solved_state is None or isinstance(solved_state, tuple):
        raise PricingError("py_pde solver did not return a scalar field state.")
    final_state = cast(pde.ScalarField, solved_state)

    price = float(final_state.interpolate(np.asarray([spot_log], dtype=float)))
    if not math.isfinite(price) or price < 0.0:
        raise PricingError(
            "py_pde solver produced an invalid option value.",
            details=str(price),
            suggestion="Adjust numerical settings and check model parameters.",
        )

    return PricingResult(
        price=price,
        backend="py_pde",
        engine="CrankNicolsonBlackScholes1D",
        metadata={
            "time_steps": time_steps,
            "space_steps": space_steps,
            "maturity_years": maturity_years,
            "log_lower_bound": log_lower_bound,
            "log_upper_bound": log_upper_bound,
        },
    )
