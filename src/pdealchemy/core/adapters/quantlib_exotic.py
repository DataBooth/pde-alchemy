"""Exotic QuantLib pricing route internals."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.adapters.quantlib_market import _market_inputs, _time_key
from pdealchemy.core.models import PricingResult
from pdealchemy.exceptions import PricingError


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
    spot, strike, risk_free_rate, volatility, dividend_yield = _market_inputs(
        config_data,
        require_flat_market_inputs=True,
    )
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
