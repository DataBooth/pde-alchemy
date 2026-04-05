# PDEAlchemy
PDEAlchemy is a CLI-first framework for pricing financial options with PDE solvers, starting from transparent TOML configurations.
Abbreviation: `PDA` (pronounced “pee-dee-ay”), with a playful nod to “Personal Digital Assistant”.

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
- Vanilla with market curve/surface inputs: `examples/vanilla_market_curve_surface.toml`

## CLI Examples
```bash
uv run pdealchemy validate path/to/config.toml
uv run pdealchemy explain path/to/config.toml --format markdown
uv run pdealchemy validate path/to/config.toml --analytical --tolerance 0.75
uv run pdealchemy price path/to/config.toml
```

Convenience `just` recipes for the main workflows:
```bash
just price
just validate
just explain
```

## Market Curves and Surfaces
QuantLib vanilla pricing routes can now consume optional market structures from TOML:
- Flat or node-based zero-rate curves for risk-free and dividend term structures
- Constant volatility, volatility term curves, or volatility surfaces

See `examples/vanilla_market_curve_surface.toml` for a complete configuration.

Current limitation:
- Exotic Monte Carlo routes currently require flat curves and constant volatility.

## marimo Notebook Explorer
An interactive marimo notebook example is available at `examples/notebooks/price_explorer.py`.

Launch it with either command:
```bash
just notebook
```

```bash
uv run marimo edit examples/notebooks/price_explorer.py
```

Run it in app mode:
```bash
just notebook-run
```

Quick notebook static check:
```bash
just notebook-check
```

`just notebook-run` starts a server and keeps running until interrupted. Exiting with Ctrl-C returns code `130`, which is expected behaviour.

## Lint, Type Checks, and Pre-Commit
Ruff and ty are configured for progressive quality enforcement:
- Source code (`src/`) is checked for docstrings and type annotations.
- Tests are temporarily excluded from strict docstring/type-hint linting while coverage is improved incrementally.

Commands:
```bash
just lint
just typecheck
just check
```

Pre-commit setup:
```bash
just precommit-install
just precommit-run
```

## Validation Strategy
- Philosophy: `VALIDATION_PHILOSOPHY.md`
- Practical strategy and trust boundaries: `docs/validation_strategy.md`
- Data source purpose and limitations: `docs/market_data_sources.md`

## Development Blog
The project now keeps a progressive engineering log under `docs/blog/`.

Start here:
- `docs/blog/README.md`
