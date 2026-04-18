default:
    @just --list

install:
    uv sync --all-extras --dev

test:
    uv run pytest
test-cov:
    uv run pytest --cov=src/pdealchemy --cov-report=term-missing --cov-report=xml

lint:
    uv run ruff check src tests
typecheck:
    uv run ty check src

format:
    uv run ruff format src tests

check:
    just lint
    just typecheck
    just test-cov

run *args:
    uv run pdealchemy {{args}}
price config="examples/vanilla_european_call.toml":
    uv run pdealchemy price {{config}}

validate config="examples/vanilla_european_call.toml" *args:
    uv run pdealchemy validate {{config}} {{args}}

explain config="examples/vanilla_european_call.toml" format="markdown":
    uv run pdealchemy explain {{config}} --format {{format}}

notebook file="examples/notebooks/price_explorer.py":
    uv run --extra interactive marimo edit {{file}}

notebook-run file="examples/notebooks/price_explorer.py":
    uv run --extra interactive marimo run {{file}}

notebook-check file="examples/notebooks/price_explorer.py":
    uv run --extra interactive marimo check {{file}}
notebook-to-toml notebook="examples/notebooks/spec_black_scholes.py" output="examples/notebooks/black_scholes_blueprint.toml":
    uv run pdealchemy notebook-to-toml {{notebook}} --output {{output}} --overwrite
spec-to-runtime-toml spec="examples/notebooks/black_scholes_blueprint.toml" output="examples/notebooks/black_scholes_pricing.toml":
    uv run pdealchemy spec-to-runtime-toml {{spec}} --output {{output}} --overwrite

bs-e2e notebook="examples/notebooks/spec_black_scholes.py" spec_output="examples/notebooks/black_scholes_blueprint.toml" runtime_output="examples/notebooks/black_scholes_pricing.toml" explain_format="markdown":
    uv run pdealchemy notebook-to-toml {{notebook}} --output {{spec_output}} --overwrite
    uv run pdealchemy spec-to-runtime-toml {{spec_output}} --output {{runtime_output}} --overwrite
    uv run pdealchemy validate {{runtime_output}} --equation-library library
    uv run pdealchemy validate {{runtime_output}} --analytical --tolerance 0.75
    uv run pdealchemy price {{runtime_output}}
    uv run pdealchemy explain {{runtime_output}} --format {{explain_format}}

bs-results:
    uv run --extra interactive marimo edit examples/notebooks/black_scholes_results.py

bs-spec-results:
    uv run --extra interactive marimo edit examples/notebooks/spec_black_scholes_with_results.py

precommit-install:
    uv run pre-commit install

precommit-run:
    uv run pre-commit run --all-files
