"""Bridge notebook specification TOML into executable runtime TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pdealchemy.exceptions import ConfigError

_BASELINE_SDE_FILE = "library/sde/black_scholes_geometric_brownian_motion.md"
_BASELINE_PDE_FILE = "library/pde/black_scholes.md"
_BASELINE_PAYOFF_FILE = "library/payoff/vanilla_call.md"
_BASELINE_RATE_FILE = "library/data/rates_flat.md"
_BASELINE_VOL_FILE = "library/data/volatility_constant.md"
_BASELINE_DISCRETISATION_FILE = "library/discretisation/crank_nicolson_standard.md"
_SUPPORTED_BACKENDS = {"quantlib", "py_pde"}


@dataclass(frozen=True)
class BlackScholesBridgeDefaults:
    """Runtime defaults used when bridging spec TOML into pricing TOML."""

    spot: float = 100.0
    strike: float = 100.0
    rate: float = 0.05
    volatility: float = 0.2
    maturity: float = 1.0
    backend: str = "quantlib"
    scheme: str = "crank_nicolson"
    time_steps: int = 250
    damping_steps: int = 0
    grid_lower: float = 0.0
    grid_upper: float = 400.0
    grid_points: int = 401
    monte_carlo_paths: int = 20_000
    monte_carlo_seed: int = 1234
    monte_carlo_antithetic: bool = True


def _render_toml_string(value: str) -> str:
    """Render a TOML string with support for multiline content."""
    if "\n" in value:
        escaped = value.replace("'''", "\\'\\'\\'")
        return f"'''\n{escaped}\n'''"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_toml_float(value: float) -> str:
    """Render a float with stable TOML-friendly formatting."""
    rendered = f"{value:.12g}"
    if "e" not in rendered and "." not in rendered:
        rendered = f"{rendered}.0"
    return rendered


def _load_toml_mapping(toml_path: Path) -> dict[str, object]:
    """Load TOML data and ensure the root object is a table."""
    if not toml_path.exists():
        raise ConfigError(
            f"TOML file not found: {toml_path}",
            suggestion="Check the path and try again.",
        )
    if not toml_path.is_file():
        raise ConfigError(
            f"TOML path is not a file: {toml_path}",
            suggestion="Provide a path to a TOML file.",
        )
    try:
        with toml_path.open("rb") as file_obj:
            raw_data = tomllib.load(file_obj)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            "TOML file is not valid TOML.",
            details=str(exc),
            suggestion="Fix TOML syntax and re-run the command.",
        ) from exc
    if not isinstance(raw_data, dict):
        raise ConfigError(
            "TOML root must be a table.",
            suggestion="Ensure the TOML file contains top-level tables.",
        )
    return raw_data


def _table(mapping: dict[str, object], key: str, *, context: str) -> dict[str, object]:
    """Return a nested TOML table and validate its type."""
    maybe_table = mapping.get(key)
    if not isinstance(maybe_table, dict):
        raise ConfigError(
            f"Spec table is missing or invalid: [{context}]",
            suggestion="Ensure notebook-to-toml output contains the required semantic sections.",
        )
    return cast(dict[str, object], maybe_table)


def _string(
    mapping: dict[str, object],
    key: str,
    *,
    context: str,
    required: bool = True,
) -> str | None:
    """Extract a string value from a TOML table."""
    value = mapping.get(key)
    if value is None:
        if required:
            raise ConfigError(
                f"Spec field is missing: [{context}] {key}",
                suggestion="Ensure the source notebook provides this semantic field.",
            )
        return None
    if not isinstance(value, str):
        raise ConfigError(
            f"Spec field has invalid type: [{context}] {key}",
            details=f"Expected string, received {type(value).__name__}.",
            suggestion="Re-run notebook-to-toml and verify semantic cell helpers.",
        )
    return value.strip()


def _require_expected_file(
    *,
    table_mapping: dict[str, object],
    context: str,
    expected_path: str,
) -> None:
    """Validate that a semantic section points at the expected baseline file."""
    equation_file = _string(table_mapping, "equation_file", context=context)
    if equation_file != expected_path:
        raise ConfigError(
            f"Unsupported baseline mapping for [{context}].",
            details=f"Expected `{expected_path}`, received `{equation_file}`.",
            suggestion=(
                "Current schema bridge supports the canonical Black-Scholes baseline files "
                "only. Use the template/example library paths."
            ),
        )


def _normalise_runtime_name(spec_name: str) -> str:
    """Convert a notebook specification title into a runtime config title."""
    suffix = "— Specification"
    if spec_name.endswith(suffix):
        return spec_name.removesuffix(suffix).rstrip()
    return spec_name


def _validate_defaults(defaults: BlackScholesBridgeDefaults) -> None:
    """Validate bridge defaults before rendering runtime TOML."""
    if defaults.backend not in _SUPPORTED_BACKENDS:
        allowed = ", ".join(sorted(_SUPPORTED_BACKENDS))
        raise ConfigError(
            "Unsupported runtime backend.",
            details=f"Received `{defaults.backend}`.",
            suggestion=f"Use one of: {allowed}.",
        )
    if defaults.maturity <= 0.0:
        raise ConfigError("maturity must be positive.")
    if defaults.time_steps <= 0:
        raise ConfigError("time_steps must be positive.")
    if defaults.grid_points < 3:
        raise ConfigError("grid_points must be at least 3.")
    if defaults.grid_lower >= defaults.grid_upper:
        raise ConfigError("grid_lower must be less than grid_upper.")
    if defaults.monte_carlo_paths <= 0:
        raise ConfigError("monte_carlo_paths must be positive.")
    if defaults.damping_steps < 0:
        raise ConfigError("damping_steps must be >= 0.")


def spec_to_runtime_toml_content(
    spec_toml_path: Path,
    *,
    defaults: BlackScholesBridgeDefaults | None = None,
) -> str:
    """Bridge notebook spec TOML into executable Black-Scholes runtime TOML."""
    runtime_defaults = defaults or BlackScholesBridgeDefaults()
    _validate_defaults(runtime_defaults)
    raw_data = _load_toml_mapping(spec_toml_path)

    metadata = _table(raw_data, "metadata", context="metadata")
    instrument = _table(raw_data, "instrument", context="instrument")
    mathematics = _table(raw_data, "mathematics", context="mathematics")
    mathematics_sde = _table(mathematics, "sde", context="mathematics.sde")
    mathematics_operator = _table(mathematics, "operator", context="mathematics.operator")
    payoff = _table(raw_data, "payoff", context="payoff")
    numerics = _table(raw_data, "numerics", context="numerics")
    data = _table(raw_data, "data", context="data")
    data_rates = _table(data, "rates", context="data.rates")
    data_volatility = _table(data, "volatility", context="data.volatility")

    _require_expected_file(
        table_mapping=mathematics_sde,
        context="mathematics.sde",
        expected_path=_BASELINE_SDE_FILE,
    )
    _require_expected_file(
        table_mapping=mathematics_operator,
        context="mathematics.operator",
        expected_path=_BASELINE_PDE_FILE,
    )
    _require_expected_file(
        table_mapping=payoff,
        context="payoff",
        expected_path=_BASELINE_PAYOFF_FILE,
    )
    _require_expected_file(
        table_mapping=data_rates,
        context="data.rates",
        expected_path=_BASELINE_RATE_FILE,
    )
    _require_expected_file(
        table_mapping=data_volatility,
        context="data.volatility",
        expected_path=_BASELINE_VOL_FILE,
    )

    discretisation_file = _string(numerics, "markdown_file", context="numerics")
    if discretisation_file != _BASELINE_DISCRETISATION_FILE:
        raise ConfigError(
            "Unsupported baseline mapping for [numerics].",
            details=(
                "Expected canonical discretisation file "
                f"`{_BASELINE_DISCRETISATION_FILE}`, received `{discretisation_file}`."
            ),
            suggestion="Use the canonical Crank-Nicolson discretisation markdown file.",
        )

    specification_name = _string(metadata, "name", context="metadata")
    if specification_name is None:  # pragma: no cover - guarded by required=True
        raise ConfigError("Spec field is missing: [metadata] name")
    runtime_name = _normalise_runtime_name(specification_name)
    instrument_description = _string(
        instrument,
        "description",
        context="instrument",
        required=False,
    )
    runtime_description_parts = [
        f"Runtime configuration bridged from {spec_toml_path.name}.",
    ]
    if instrument_description:
        runtime_description_parts.append(instrument_description)

    lines = [
        f"# Generated from {spec_toml_path.name} by pdealchemy spec-to-runtime-toml",
        "",
        "[metadata]",
        f"name = {_render_toml_string(runtime_name)}",
        f"description = {_render_toml_string(' '.join(runtime_description_parts))}",
        'tags = ["notebook-bridge", "black-scholes", "vanilla"]',
        "",
        "[process]",
        'state_variables = ["S"]',
        (
            "parameters = { "
            f"S0 = {_render_toml_float(runtime_defaults.spot)}, "
            f"r = {_render_toml_float(runtime_defaults.rate)}, "
            f"sigma = {_render_toml_float(runtime_defaults.volatility)}, "
            f"K = {_render_toml_float(runtime_defaults.strike)} "
            "}"
        ),
        'drift = { S = "r * S" }',
        'diffusion = { S = "sigma * S" }',
        "",
        "[instrument]",
        'kind = "vanilla_option"',
        'payoff = "max(S - K, 0)"',
        f"maturity = {_render_toml_float(runtime_defaults.maturity)}",
        'exercise = "european"',
        'style = "call"',
        "",
        "[numerics]",
        f'backend = "{runtime_defaults.backend}"',
        f'scheme = "{runtime_defaults.scheme}"',
        f"time_steps = {runtime_defaults.time_steps}",
        f"damping_steps = {runtime_defaults.damping_steps}",
        "",
        "[numerics.grid]",
        f"lower = {{ S = {_render_toml_float(runtime_defaults.grid_lower)} }}",
        f"upper = {{ S = {_render_toml_float(runtime_defaults.grid_upper)} }}",
        f"points = {{ S = {runtime_defaults.grid_points} }}",
        "",
        "[numerics.monte_carlo]",
        f"paths = {runtime_defaults.monte_carlo_paths}",
        f"seed = {runtime_defaults.monte_carlo_seed}",
        f"antithetic = {'true' if runtime_defaults.monte_carlo_antithetic else 'false'}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def spec_to_runtime_toml_file(
    spec_toml_path: Path,
    *,
    output_path: Path | None = None,
    overwrite: bool = False,
    defaults: BlackScholesBridgeDefaults | None = None,
) -> Path:
    """Write runtime TOML bridged from spec TOML and return the output path."""
    rendered = spec_to_runtime_toml_content(spec_toml_path, defaults=defaults)
    default_output_path = spec_toml_path.with_name(f"{spec_toml_path.stem}.pricing.toml")
    if spec_toml_path.stem.endswith("_blueprint"):
        default_output_path = spec_toml_path.with_name(
            f"{spec_toml_path.stem.removesuffix('_blueprint')}_pricing.toml"
        )
    target_path = output_path if output_path is not None else default_output_path
    if target_path.exists() and not overwrite:
        raise ConfigError(
            f"Output file already exists: {target_path}",
            suggestion="Use --overwrite to replace it or provide --output <path>.",
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(rendered, encoding="utf-8")
    return target_path
