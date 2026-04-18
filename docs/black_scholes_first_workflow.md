# Black-Scholes-first workflow
Use this workflow to validate the project from the simplest stable baseline, then expand scope gradually.

## 0) Environment setup
- `uv sync --all-extras --dev`
- `just check`

## 1) Baseline vanilla TOML
Start with the canonical Black-Scholes-style vanilla config.

- `uv run pdealchemy validate examples/vanilla_european_call.toml`
- `uv run pdealchemy price examples/vanilla_european_call.toml`
- `uv run pdealchemy explain examples/vanilla_european_call.toml --format markdown`

Expected outcome:
- validation success,
- stable price output from the selected backend,
- readable explain output with consistent symbols.

## 2) Analytical benchmark
Cross-check the vanilla route against the analytical benchmark.

- `uv run pdealchemy validate examples/vanilla_european_call.toml --analytical --tolerance 0.75`

If this fails:
- confirm the config still represents a non-exotic European vanilla route,
- inspect numerical settings and tolerance.

## 3) Equation-library constrained validation
Validate Markdown equations in `library/` against the constrained LaTeX subset.

- `uv run pdealchemy validate examples/vanilla_european_call.toml --equation-library library`

This catches:
- unsupported LaTeX commands,
- malformed algebraic equation blocks.

## 4) Notebook-driven spec and runtime bridge baseline
Validate the notebook-to-TOML path, then bridge to executable runtime TOML.

- `uv run pdealchemy notebook-to-toml examples/notebooks/spec_black_scholes.py --output examples/notebooks/black_scholes_blueprint.toml --overwrite`
- `uv run pdealchemy spec-to-runtime-toml examples/notebooks/black_scholes_blueprint.toml --output examples/notebooks/black_scholes_pricing.toml --overwrite`
- `uv run pdealchemy validate examples/notebooks/black_scholes_pricing.toml --equation-library library`
- `uv run pdealchemy validate examples/notebooks/black_scholes_pricing.toml --analytical --tolerance 0.75`
- `uv run pdealchemy price examples/notebooks/black_scholes_pricing.toml`
- `uv run pdealchemy explain examples/notebooks/black_scholes_pricing.toml --format markdown`

## 5) Optional one-command baseline run
- `just bs-e2e`

## 6) Optional reporting notebooks
- Results notebook with selectable sections and table/chart outputs:
  - `just notebook examples/notebooks/black_scholes_results.py`
- Combined notebook with specification content followed by outputs:
  - `just notebook examples/notebooks/spec_black_scholes_with_results.py`

## 7) Expand incrementally
After baseline confidence, expand in this order:
1. market-structure vanilla route: `examples/vanilla_market_curve_surface.toml`
2. exotic path-dependent route: `examples/exotic_discrete_asian_barrier_dividend.toml`

Keep each expansion step deterministic and test-backed before moving to the next.
