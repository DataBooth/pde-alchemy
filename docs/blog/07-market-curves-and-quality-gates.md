# 07 — Market Curves, Surfaces, and Progressive Quality Gates
## What we implemented
- Added optional market schema support for:
  - flat and zero-rate curves,
  - constant volatility, volatility term curves, and volatility surfaces.
- Integrated these market structures into the QuantLib vanilla pricing route.
- Added canonical market example config and corresponding integration tests.
- Added progressive code quality tooling:
  - Ruff docstring and annotation checks for source modules,
  - ty type-checking for source modules,
  - pre-commit hooks for Ruff and ty.

## Key design decisions
- Keep market modelling declarative in config and compile it in the adapter layer.
- Reuse QuantLib term-structure primitives instead of implementing custom interpolation maths.
- Keep exotic Monte Carlo routes constrained to flat market inputs for now to avoid false precision.
- Enforce stricter quality checks progressively, starting with `src/` before extending to tests.

## Validation approach
- Added schema tests for market structure shape/ordering and maturity consistency.
- Added pricing integration tests for vanilla curve/surface inputs.
- Added guardrail tests for unsupported exotic market combinations.
- Retained trust-boundary discipline: validate orchestration and mapping logic; trust QuantLib numerics.

## Usage snapshot
- `uv run pdealchemy price examples/vanilla_market_curve_surface.toml`
- `just typecheck`
- `just precommit-run`

## Lessons learned
- A thin market schema layer provides flexibility without over-committing to data-provider specifics.
- Progressive lint/type adoption works best when combined with explicit, documented boundaries.
