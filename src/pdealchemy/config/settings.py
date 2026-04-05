"""Runtime settings model driven by environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from pdealchemy.config.models import SolverBackend


class AppSettings(BaseSettings):
    """Global runtime settings for CLI behaviour and defaults."""

    model_config = SettingsConfigDict(
        env_prefix="PDEALCHEMY_",
        extra="ignore",
    )

    default_backend: SolverBackend = "quantlib"
    default_explain_format: Literal["text", "markdown", "latex"] = "text"
    default_log_level: Literal["WARNING", "INFO", "DEBUG"] = "WARNING"
    json_logs: bool = False
