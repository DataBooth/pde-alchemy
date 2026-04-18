"""Shared helpers for deterministic TOML value rendering."""

from __future__ import annotations


def render_toml_string(value: str) -> str:
    """Render a TOML string with support for multiline content."""
    if "\n" in value:
        escaped = value.replace("'''", "\\'\\'\\'")
        return f"'''\n{escaped}\n'''"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
