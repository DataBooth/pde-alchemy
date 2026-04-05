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
