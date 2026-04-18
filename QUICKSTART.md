# PDEAlchemy Quickstart (Black-Scholes notebook-first)
This guide walks through the fastest path from the specification notebook to a validated Black-Scholes baseline run.

## 1) Install and verify the environment
```bash
uv sync --all-extras --dev
just check
```

## 2) Start from the specification notebook
Open the canonical notebook:
```bash
just notebook examples/notebooks/spec_black_scholes.py
```

The notebook is the authoring entry point for:
- instrument and assumptions,
- risk-neutral SDE and pricing PDE,
- payoff and boundary conditions,
- constant-rate and constant-volatility data references.

## 3) Convert notebook spec to TOML
Export the notebook semantics into TOML:
```bash
uv run pdealchemy notebook-to-toml examples/notebooks/spec_black_scholes.py --output examples/notebooks/spec_black_scholes.toml --overwrite
```

## 4) Validate the equation library
Run constrained LaTeX validation for equations in `library/`:
```bash
uv run pdealchemy validate examples/vanilla_european_call.toml --equation-library library
```

## 5) Run the baseline Black-Scholes runtime config
Use the canonical runtime config for pricing and explainability checks:
```bash
uv run pdealchemy validate examples/vanilla_european_call.toml
uv run pdealchemy validate examples/vanilla_european_call.toml --analytical --tolerance 0.75
uv run pdealchemy price examples/vanilla_european_call.toml
uv run pdealchemy explain examples/vanilla_european_call.toml --format markdown
```

## Current status of notebook-to-runtime flow
At present, notebook-generated TOML captures specification structure but is not yet a direct runtime pricing config.

Use:
- notebook TOML for specification capture and review, and
- `examples/vanilla_european_call.toml` (or equivalent runtime TOML) for executable validation and pricing.

## Next expansion steps
After the baseline is stable, expand in order:
1. `examples/vanilla_market_curve_surface.toml`
2. `examples/exotic_discrete_asian_barrier_dividend.toml`
