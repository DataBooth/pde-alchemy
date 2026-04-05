"""Backend dispatcher for pricing requests."""

from __future__ import annotations

from pdealchemy.config.models import PricingConfig
from pdealchemy.core.adapters.py_pde import price_with_py_pde
from pdealchemy.core.adapters.quantlib import price_with_quantlib
from pdealchemy.core.models import PricingResult
from pdealchemy.exceptions import PricingError
from pdealchemy.math_bridge import build_symbolic_problem


def price_config(config_data: PricingConfig) -> PricingResult:
    """Price option using the configured numerical backend."""
    _ = build_symbolic_problem(config_data)

    if config_data.numerics.backend == "quantlib":
        return price_with_quantlib(config_data)
    if config_data.numerics.backend == "py_pde":
        return price_with_py_pde(config_data)

    raise PricingError(
        "Unsupported pricing backend.",
        details=config_data.numerics.backend,
        suggestion="Use one of: quantlib, py_pde.",
    )
