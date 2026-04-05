default:
    @just --list

install:
    uv sync --all-extras --dev

test:
    uv run pytest

lint:
    uv run ruff check src tests

format:
    uv run ruff format src tests

check:
    just lint
    just test

run *args:
    uv run pdealchemy {{args}}

notebook file="examples/notebooks/price_explorer.py":
    uv run marimo edit {{file}}

notebook-run file="examples/notebooks/price_explorer.py":
    uv run marimo run {{file}}
