"""Tests for logging configuration wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdealchemy import logging_config


class FakeLogger:
    def __init__(self) -> None:
        self.remove_calls = 0
        self.add_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def remove(self) -> None:
        self.remove_calls += 1

    def add(self, *args: object, **kwargs: object) -> int:
        self.add_calls.append((args, kwargs))
        return len(self.add_calls)


def test_configure_logging_default_level(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = FakeLogger()
    monkeypatch.setattr(logging_config, "logger", fake_logger)

    logging_config.configure_logging()

    assert fake_logger.remove_calls == 1
    assert len(fake_logger.add_calls) == 1
    output_args, output_kwargs = fake_logger.add_calls[0]
    assert output_args[0] is logging_config.sys.stdout
    assert output_kwargs["level"] == "WARNING"
    assert output_kwargs["serialize"] is False
    assert output_kwargs["backtrace"] is False
    assert output_kwargs["diagnose"] is False
    assert output_kwargs["colorize"] is True


def test_configure_logging_verbose_level(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = FakeLogger()
    monkeypatch.setattr(logging_config, "logger", fake_logger)

    logging_config.configure_logging(verbose=True)

    assert len(fake_logger.add_calls) == 1
    assert fake_logger.add_calls[0][1]["level"] == "INFO"


def test_configure_logging_debug_with_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = FakeLogger()
    log_path = tmp_path / "pdealchemy.log"
    monkeypatch.setattr(logging_config, "logger", fake_logger)

    logging_config.configure_logging(debug=True, json_logs=True, log_file=log_path)

    assert fake_logger.remove_calls == 1
    assert len(fake_logger.add_calls) == 2

    console_args, console_kwargs = fake_logger.add_calls[0]
    assert console_args[0] is logging_config.sys.stdout
    assert console_kwargs["level"] == "DEBUG"
    assert console_kwargs["serialize"] is True
    assert console_kwargs["backtrace"] is True
    assert console_kwargs["diagnose"] is True
    assert console_kwargs["colorize"] is False

    file_args, file_kwargs = fake_logger.add_calls[1]
    assert file_args[0] == log_path
    assert file_kwargs["level"] == "DEBUG"
    assert file_kwargs["serialize"] is True
    assert file_kwargs["rotation"] == "5 MB"
    assert file_kwargs["retention"] == 5
    assert file_kwargs["backtrace"] is True
    assert file_kwargs["diagnose"] is True
