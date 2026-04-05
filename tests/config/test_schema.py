"""Tests for schema export helpers."""

from __future__ import annotations

import json
from pathlib import Path

from pdealchemy.config.schema import (
    pricing_config_json_schema,
    write_pricing_config_json_schema,
)


def test_pricing_schema_contains_expected_sections() -> None:
    schema = pricing_config_json_schema()
    properties = schema["properties"]

    assert "process" in properties
    assert "instrument" in properties
    assert "numerics" in properties
    assert "market" in properties


def test_write_pricing_schema_to_disk(tmp_path: Path) -> None:
    output_path = tmp_path / "schema" / "pdealchemy.schema.json"
    write_pricing_config_json_schema(output_path)

    assert output_path.exists()
    loaded_schema = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded_schema["title"] == "PricingConfig"
