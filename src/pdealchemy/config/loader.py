"""Configuration loading and validation utilities."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pdealchemy.config.models import PricingConfig
from pdealchemy.exceptions import ConfigError
from pdealchemy.math_bridge.problem import SymbolicPricingProblem, build_symbolic_problem


def _format_validation_errors(error: PydanticValidationError) -> str:
    """Render pydantic errors in a compact, readable form."""
    rendered: list[str] = []
    max_errors = 8
    errors = error.errors()

    for issue in errors[:max_errors]:
        location = ".".join(str(part) for part in issue["loc"])
        rendered.append(f"- {location}: {issue['msg']}")

    if len(errors) > max_errors:
        remaining = len(errors) - max_errors
        rendered.append(f"- ... and {remaining} more issue(s).")

    return "\n".join(rendered)


def _load_toml_file(config_path: Path) -> dict[str, Any]:
    """Load raw TOML data from disk."""
    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {config_path}",
            suggestion="Check the path and try again.",
        )
    if not config_path.is_file():
        raise ConfigError(
            f"Configuration path is not a file: {config_path}",
            suggestion="Provide a path to a TOML file.",
        )

    try:
        with config_path.open("rb") as file_obj:
            raw_data = tomllib.load(file_obj)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            "Configuration file is not valid TOML.",
            details=str(exc),
            suggestion="Fix TOML syntax and re-run `pdealchemy validate`.",
        ) from exc

    if not isinstance(raw_data, dict):
        raise ConfigError(
            "Configuration root must be a TOML table.",
            suggestion="Ensure the file contains key/value sections at top level.",
        )

    return raw_data


def load_pricing_config(config_path: Path) -> PricingConfig:
    """Load and validate TOML into a strongly typed pricing config."""
    raw_data = _load_toml_file(config_path)
    try:
        return PricingConfig.model_validate(raw_data)
    except PydanticValidationError as exc:
        raise ConfigError(
            "Configuration file failed schema validation.",
            details=_format_validation_errors(exc),
            suggestion="Run `pdealchemy explain <config.toml>` to inspect parsed sections.",
        ) from exc


def load_symbolic_problem(config_path: Path) -> SymbolicPricingProblem:
    """Load TOML and build parsed symbolic expressions."""
    return build_symbolic_problem(load_pricing_config(config_path))
