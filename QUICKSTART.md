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

## 4) Bridge spec TOML to runtime TOML
Generate an executable pricing config from the notebook spec artefact:
```bash
uv run pdealchemy spec-to-runtime-toml examples/notebooks/spec_black_scholes.toml --output examples/notebooks/spec_black_scholes.runtime.toml --overwrite
```

## 5) Validate the equation library
Run constrained LaTeX validation for equations in `library/` together with runtime schema checks:
```bash
uv run pdealchemy validate examples/notebooks/spec_black_scholes.runtime.toml --equation-library library
```

## 6) Run baseline pricing and explain outputs
Use the bridged runtime config for pricing and explainability checks:
```bash
uv run pdealchemy validate examples/notebooks/spec_black_scholes.runtime.toml --analytical --tolerance 0.75
uv run pdealchemy price examples/notebooks/spec_black_scholes.runtime.toml
uv run pdealchemy explain examples/notebooks/spec_black_scholes.runtime.toml --format markdown
```

## 7) Optional: run the full baseline chain in one command
```bash
just bs-e2e
```

## 8) Optional: capture outputs in a results notebook
```bash
just notebook examples/notebooks/black_scholes_results.py
```
This notebook supports selectable sections (pricing, sensitivities, sweeps, validation, explain) and render modes (tables and/or Plotly charts).

## 9) Optional: use one notebook with spec content followed by outputs
```bash
just notebook examples/notebooks/spec_black_scholes_with_results.py
```

Output artefact content and format guidance is documented in `docs/output_specification.md`.

## Next expansion steps
After the baseline is stable, expand in order:
1. `examples/vanilla_market_curve_surface.toml`
2. `examples/exotic_discrete_asian_barrier_dividend.toml`
