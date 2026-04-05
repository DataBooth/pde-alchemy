"""JSON-schema helpers for PDEAlchemy configuration models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pdealchemy.config.models import PricingConfig


def pricing_config_json_schema() -> dict[str, Any]:
    """Return JSON schema for the canonical pricing config model."""
    return PricingConfig.model_json_schema()


def write_pricing_config_json_schema(output_path: Path) -> None:
    """Write pricing config schema to disk for editor integration."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema_json = json.dumps(pricing_config_json_schema(), indent=2, sort_keys=True)
    output_path.write_text(f"{schema_json}\n", encoding="utf-8")
