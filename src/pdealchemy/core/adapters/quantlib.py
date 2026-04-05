"""QuantLib finite-difference adapter and Monte Carlo exotic route."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable

import numpy as np
import QuantLib

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.models import PricingResult
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


def _option_type(style: str) -> QuantLib.Option.Type:
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


def _market_inputs(config_data: PricingConfig) -> tuple[float, float, float, float, float]:
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
    dividend_curve = QuantLib.YieldTermStructureHandle(
        QuantLib.FlatForward(evaluation_date, dividend_yield, day_count)
    )
    risk_free_curve = QuantLib.YieldTermStructureHandle(
        QuantLib.FlatForward(evaluation_date, risk_free_rate, day_count)
    )
    volatility_curve = QuantLib.BlackVolTermStructureHandle(
        QuantLib.BlackConstantVol(evaluation_date, calendar, volatility, day_count)
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
        },
    )


def _time_grid(
    maturity: float,
    time_steps: int,
    observation_times: list[float],
    dividend_times: list[float],
) -> list[float]:
    base_grid = [index * maturity / time_steps for index in range(time_steps + 1)]
    all_times = [*base_grid, *observation_times, *dividend_times, maturity]
    deduped = {_time_key(time_value): time_value for time_value in all_times}
    ordered = sorted(deduped.items(), key=lambda item: item[0])
    return [time_value for _, time_value in ordered]


def _draw_normals(
    rng: np.random.Generator,
    count: int,
    *,
    antithetic: bool,
) -> np.ndarray:
    if not antithetic:
        return rng.standard_normal(count)

    half_count = (count + 1) // 2
    half_values = rng.standard_normal(half_count)
    reflected = -half_values
    combined = np.concatenate([half_values, reflected])
    return combined[:count]


def _apply_barrier_hits(
    barrier_type: str,
    level: float,
    spot_values: np.ndarray,
    knocked_out: np.ndarray,
) -> None:
    if barrier_type == "up_and_out":
        knocked_out |= spot_values >= level
    elif barrier_type == "down_and_out":
        knocked_out |= spot_values <= level
    else:
        raise PricingError(
            "Unsupported barrier type in Monte Carlo adapter.",
            details=barrier_type,
        )


def _price_exotic_monte_carlo(config_data: PricingConfig, *, style: str) -> PricingResult:
    """Price path-dependent combinations with Monte Carlo simulation."""
    spot, strike, risk_free_rate, volatility, dividend_yield = _market_inputs(config_data)
    maturity = config_data.instrument.maturity
    features = config_data.features
    if features is None:
        raise PricingError("Missing features section for exotic Monte Carlo route.")

    asian = features.asian
    barrier = features.barrier
    dividends = [] if features.dividends is None else features.dividends.events

    observation_times = [] if asian is None else list(asian.observation_times)
    dividend_times = [event.time for event in dividends]
    dividend_by_time: dict[float, list[float]] = defaultdict(list)
    for event in dividends:
        dividend_by_time[_time_key(event.time)].append(event.amount)

    time_grid = _time_grid(
        maturity,
        config_data.numerics.time_steps,
        observation_times,
        dividend_times,
    )
    observation_keys = {_time_key(value) for value in observation_times}

    paths_count = config_data.numerics.monte_carlo.paths
    rng = np.random.default_rng(config_data.numerics.monte_carlo.seed)
    antithetic = config_data.numerics.monte_carlo.antithetic

    spot_values = np.full(paths_count, spot, dtype=float)
    knocked_out = np.zeros(paths_count, dtype=bool)
    observations: list[np.ndarray] = []

    drift_rate = risk_free_rate - dividend_yield
    previous_time = time_grid[0]

    for current_time in time_grid[1:]:
        delta_time = current_time - previous_time
        if delta_time < 0.0:
            raise PricingError("Time grid must be non-decreasing.")

        if delta_time > 0.0:
            normals = _draw_normals(rng, paths_count, antithetic=antithetic)
            growth = (drift_rate - 0.5 * volatility * volatility) * delta_time
            diffusion = volatility * math.sqrt(delta_time) * normals
            spot_values *= np.exp(growth + diffusion)

        if barrier is not None:
            _apply_barrier_hits(
                barrier.type,
                barrier.level,
                spot_values,
                knocked_out,
            )

        current_key = _time_key(current_time)
        if current_key in dividend_by_time:
            for amount in dividend_by_time[current_key]:
                spot_values = np.maximum(spot_values - amount, 1e-12)
            if barrier is not None:
                _apply_barrier_hits(
                    barrier.type,
                    barrier.level,
                    spot_values,
                    knocked_out,
                )

        if current_key in observation_keys:
            observations.append(spot_values.copy())

        previous_time = current_time

    if asian is not None:
        if not observations:
            raise PricingError(
                "Asian feature requires at least one observation on the generated time grid."
            )
        underlying_terminal = np.mean(np.stack(observations, axis=0), axis=0)
    else:
        underlying_terminal = spot_values

    if style == "call":
        payoff = np.maximum(underlying_terminal - strike, 0.0)
    else:
        payoff = np.maximum(strike - underlying_terminal, 0.0)

    if barrier is not None:
        payoff = np.where(knocked_out, barrier.rebate, payoff)

    discount_factor = math.exp(-risk_free_rate * maturity)
    price = float(discount_factor * np.mean(payoff))

    return PricingResult(
        price=price,
        backend="quantlib",
        engine="MonteCarloDiscreteAsianBarrierDividendEngine",
        metadata={
            "paths": paths_count,
            "time_steps": config_data.numerics.time_steps,
            "antithetic": int(antithetic),
            "has_asian": int(asian is not None),
            "has_barrier": int(barrier is not None),
            "has_dividends": int(bool(dividends)),
        },
    )


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
