# PDEAlchemy
PDEAlchemy is a CLI-first framework for pricing financial options with PDE solvers, starting from transparent TOML configurations.

## Current Status
Initial project skeleton is in place, including:
- `uv`-managed Python project configuration
- `just` task automation
- CLI scaffold (`price`, `validate`, `explain`)
- Base logging and error handling modules

## Quick Start
```bash
uv sync --all-extras --dev
just test
uv run pdealchemy --help
```

## Canonical Examples
- Vanilla: `examples/vanilla_european_call.toml`
- Exotic (discrete Asian + barrier + dividends): `examples/exotic_discrete_asian_barrier_dividend.toml`

## CLI Examples
```bash
uv run pdealchemy validate path/to/config.toml
uv run pdealchemy explain path/to/config.toml --format markdown
uv run pdealchemy validate path/to/config.toml --analytical --tolerance 0.75
uv run pdealchemy price path/to/config.toml
```
