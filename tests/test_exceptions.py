"""Tests for custom exception formatting."""

from __future__ import annotations

from pdealchemy.exceptions import ConfigError


def test_exception_cli_message_contains_suggestion_and_details() -> None:
    exc = ConfigError(
        "Invalid config",
        details="Expected key `instrument`.",
        suggestion="Add `[instrument]` to your TOML file.",
    )

    message = exc.to_cli_message()

    assert "Invalid config" in message
    assert "Expected key `instrument`." in message
    assert "Add `[instrument]` to your TOML file." in message
