default:
    @just --list

install:
    uv sync --all-extras --dev

test:
    uv run pytest

lint:
    uv run ruff check src tests
typecheck:
    uv run ty check src

format:
    uv run ruff format src tests

check:
    just lint
    just typecheck
    just test

run *args:
    uv run pdealchemy {{args}}
price config="examples/vanilla_european_call.toml":
    uv run pdealchemy price {{config}}

validate config="examples/vanilla_european_call.toml" *args:
    uv run pdealchemy validate {{config}} {{args}}

explain config="examples/vanilla_european_call.toml" format="markdown":
    uv run pdealchemy explain {{config}} --format {{format}}

notebook file="examples/notebooks/price_explorer.py":
    uv run marimo edit {{file}}

notebook-run file="examples/notebooks/price_explorer.py":
    uv run marimo run {{file}}

notebook-check file="examples/notebooks/price_explorer.py":
    uv run marimo check {{file}}

precommit-install:
    uv run pre-commit install

precommit-run:
    uv run pre-commit run --all-files
