# Validation Strategy
This document translates `VALIDATION_PHILOSOPHY.md` into day-to-day engineering practice.

## Scope
PDEAlchemy prioritises correctness by validating custom orchestration logic deeply while avoiding redundant re-testing of heavily pre-validated numerical libraries.

## Trust Boundaries
### Pre-validated components (smoke and integration focus)
- QuantLib numerical engines and pricing primitives.
- py-pde numerical kernels and stepping primitives.
- SymPy expression parsing and symbolic utilities.
- NumPy and SciPy foundational numerics.

### PDEAlchemy-owned components (full validation focus)
- Config schema and loader behaviour.
- Feature detection and dispatch routing.
- Symbolic bridge orchestration and render output wiring.
- Adapter integration logic (especially discrete features and edge handling).
- CLI behaviour, user-facing errors, and logging.

## Validation Depths
### Quick (developer loop)
- Targeted unit tests for changed orchestration modules.
- Focused integration checks for affected user flows.
- Fast smoke checks for notebook and CLI entry points where relevant.

### Full (pull requests and CI)
- Full unit suite.
- Analytical benchmark checks for supported vanilla routes.
- Integration checks for canonical examples.
- Coverage reporting focused on orchestration modules.

### Exotic (release confidence for path-dependent features)
- Monte Carlo cross-validation for exotic combinations.
- Regression checks against canonical golden configurations.
- Stress checks on boundary and stability-sensitive parameter sets.

## Practical Test Mapping
- `tests/config/*`: schema and loader correctness.
- `tests/math_bridge/*`: symbolic interpretation and robustness.
- `tests/render/*`: explain output correctness.
- `tests/core/*`: dispatching and adapter orchestration.
- `tests/validation/*`: benchmark and validation-runner logic.
- `tests/examples/*`: golden-path integration confidence.
- `tests/test_notebook_support.py`: notebook orchestration helpers.

## Pull Request Expectations
Each PR should:
- classify new logic by trust boundary (pre-validated vs orchestration-owned),
- add or update tests proportionate to risk,
- include a verification summary,
- mention validation decisions in the related blog post entry.

## Continuous Improvement
If routing decisions, trust assumptions, or validation depth expectations change, update both:
- `VALIDATION_PHILOSOPHY.md`
- `docs/validation_strategy.md`
