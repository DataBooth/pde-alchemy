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

Convenience `just` recipes for the main workflows:
```bash
just price
just validate
just explain
```

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

## Validation Strategy
- Philosophy: `VALIDATION_PHILOSOPHY.md`
- Practical strategy and trust boundaries: `docs/validation_strategy.md`

## Development Blog
The project now keeps a progressive engineering log under `docs/blog/`.

Start here:
- `docs/blog/README.md`
