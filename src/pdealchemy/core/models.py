"""Core result models for pricing workflows."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PricingResult:
    """Normalised output from backend pricing adapters."""

    price: float
    backend: str
    engine: str
    metadata: dict[str, float | int | str] = field(default_factory=dict)
