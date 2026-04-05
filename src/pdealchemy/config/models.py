"""Pydantic schema for PDEAlchemy TOML configuration files."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")]
PositiveFloat = Annotated[float, Field(gt=0.0)]
PositiveInt = Annotated[int, Field(gt=0)]
GridPoints = Annotated[int, Field(ge=3)]
SolverBackend = Literal["quantlib", "py_pde"]


def _validate_mapping_keys(
    mapping_name: str,
    mapping_keys: set[str],
    expected_keys: set[str],
) -> None:
    """Check mapping keys align with declared state variables."""
    if mapping_keys == expected_keys:
        return

    message_parts: list[str] = []
    missing = sorted(expected_keys - mapping_keys)
    extras = sorted(mapping_keys - expected_keys)

    if missing:
        message_parts.append(f"missing keys: {', '.join(missing)}")
    if extras:
        message_parts.append(f"unexpected keys: {', '.join(extras)}")

    detail = "; ".join(message_parts)
    raise ValueError(
        f"{mapping_name} keys must match process.state_variables ({detail})."
    )


class MetadataConfig(BaseModel):
    """Human-readable metadata for a pricing configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class ProcessConfig(BaseModel):
    """Symbolic process definition for PDE construction."""

    model_config = ConfigDict(extra="forbid")

    state_variables: list[Identifier] = Field(min_length=1)
    parameters: dict[Identifier, float] = Field(default_factory=dict)
    drift: dict[Identifier, str] = Field(min_length=1)
    diffusion: dict[Identifier, str] = Field(min_length=1)

    @field_validator("state_variables")
    @classmethod
    def validate_unique_state_variables(
        cls,
        state_variables: list[str],
    ) -> list[str]:
        """Enforce unique state variable names."""
        if len(set(state_variables)) != len(state_variables):
            raise ValueError("state_variables must be unique.")
        return state_variables

    @model_validator(mode="after")
    def validate_dynamics_keys(self) -> ProcessConfig:
        """Ensure drift and diffusion specify each state variable."""
        expected_keys = set(self.state_variables)
        _validate_mapping_keys("drift", set(self.drift), expected_keys)
        _validate_mapping_keys("diffusion", set(self.diffusion), expected_keys)
        return self


class InstrumentConfig(BaseModel):
    """Instrument-level configuration with symbolic payoff."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(default="generic_option", min_length=1)
    payoff: str = Field(min_length=1)
    maturity: PositiveFloat
    exercise: Literal["european", "american", "bermudan"] = "european"
    style: str | None = None


class GridConfig(BaseModel):
    """Per-dimension finite-difference grid setup."""

    model_config = ConfigDict(extra="forbid")

    lower: dict[Identifier, float] = Field(min_length=1)
    upper: dict[Identifier, float] = Field(min_length=1)
    points: dict[Identifier, GridPoints] = Field(min_length=1)

class MonteCarloConfig(BaseModel):
    """Monte Carlo controls for path-dependent pricing routes."""

    model_config = ConfigDict(extra="forbid")

    paths: PositiveInt = 20_000
    seed: int | None = None
    antithetic: bool = True


class NumericsConfig(BaseModel):
    """Numerical backend and discretisation settings."""

    model_config = ConfigDict(extra="forbid")

    backend: SolverBackend = "quantlib"
    scheme: str = Field(default="crank_nicolson", min_length=1)
    time_steps: PositiveInt = 200
    damping_steps: int = Field(default=0, ge=0)
    grid: GridConfig
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)


class BarrierConfig(BaseModel):
    """Barrier feature configuration."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["up_and_out", "down_and_out"]
    level: PositiveFloat
    rebate: float = 0.0


class AsianConfig(BaseModel):
    """Asian averaging feature configuration."""

    model_config = ConfigDict(extra="forbid")

    averaging: Literal["discrete_arithmetic"] = "discrete_arithmetic"
    observation_times: list[PositiveFloat] = Field(min_length=1)

    @field_validator("observation_times")
    @classmethod
    def validate_unique_observation_times(
        cls,
        observation_times: list[float],
    ) -> list[float]:
        """Enforce unique observation times."""
        if len(set(observation_times)) != len(observation_times):
            raise ValueError("observation_times must be unique.")
        return observation_times


class DividendEventConfig(BaseModel):
    """Discrete cash dividend event."""

    model_config = ConfigDict(extra="forbid")

    time: PositiveFloat
    amount: float = Field(ge=0.0)


class DividendsConfig(BaseModel):
    """Discrete dividend schedule."""

    model_config = ConfigDict(extra="forbid")

    events: list[DividendEventConfig] = Field(default_factory=list)


class FeaturesConfig(BaseModel):
    """Optional path-dependent / exotic features."""

    model_config = ConfigDict(extra="forbid")

    barrier: BarrierConfig | None = None
    asian: AsianConfig | None = None
    dividends: DividendsConfig | None = None


class PricingConfig(BaseModel):
    """Top-level pricing problem configuration."""

    model_config = ConfigDict(extra="forbid")

    metadata: MetadataConfig | None = None
    process: ProcessConfig
    instrument: InstrumentConfig
    numerics: NumericsConfig
    features: FeaturesConfig | None = None

    @model_validator(mode="after")
    def validate_cross_section_consistency(self) -> PricingConfig:
        """Ensure grid dimensions match process dimensions."""
        expected_keys = set(self.process.state_variables)
        _validate_mapping_keys("numerics.grid.lower", set(self.numerics.grid.lower), expected_keys)
        _validate_mapping_keys("numerics.grid.upper", set(self.numerics.grid.upper), expected_keys)
        _validate_mapping_keys(
            "numerics.grid.points",
            set(self.numerics.grid.points),
            expected_keys,
        )

        for variable in self.process.state_variables:
            lower_bound = self.numerics.grid.lower[variable]
            upper_bound = self.numerics.grid.upper[variable]
            if lower_bound >= upper_bound:
                raise ValueError(
                    f"numerics.grid bounds for '{variable}' must satisfy lower < upper."
                )
        if self.features is not None:
            maturity = self.instrument.maturity

            if self.features.asian is not None:
                for observation_time in self.features.asian.observation_times:
                    if observation_time > maturity:
                        raise ValueError(
                            "asian.observation_times must be <= instrument.maturity."
                        )

            if self.features.dividends is not None:
                for event in self.features.dividends.events:
                    if event.time > maturity:
                        raise ValueError(
                            "dividends.events.time must be <= instrument.maturity."
                        )

        return self


class AppConfig(BaseModel):
    """Optional app-level configuration that wraps a pricing config."""

    model_config = ConfigDict(extra="forbid")

    pricing: PricingConfig
