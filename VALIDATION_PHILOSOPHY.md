# PDEAlchemy — Validation philosophy
## Purpose
This document defines how PDEAlchemy approaches validation to achieve high correctness with minimal duplicated effort.

The framework relies on established numerical libraries for heavy lifting and concentrates local testing on orchestration, schema handling, symbolic transformations, and end-to-end behaviour.

## Core principles
1. Trust but verify strategically
- Treat widely used numerical engines as pre-validated components.
- Validate that adapters and orchestration call those engines correctly.
- Avoid re-implementing or exhaustively re-testing external solver internals.

2. Risk-based effort
- Highest scrutiny: custom logic (config, dispatcher, notebook-to-TOML conversion, math bridge, rendering, error paths).
- Medium scrutiny: thin adapters to external libraries.
- Lower scrutiny: direct delegations to mature external engines, covered by smoke and integration tests.

3. Progressive validation pyramid
- Unit tests for custom modules
- Analytical benchmarks for canonical models
- Convergence studies for numerical stability
- Monte Carlo cross-checks where appropriate
- Regression golden-set tests for representative instrument sets

4. Transparency
- Keep trust boundaries explicit in docs.
- Report failures with actionable diagnostics.
- Keep validation docs and examples aligned with actual workflows.

## Component classification
### Pre-validated layers (minimal re-testing)
- QuantLib-Python finite-difference and Monte Carlo engines
- py-pde core discretisation and stepping machinery
- SymPy symbolic manipulation and lambdify
- NumPy/SciPy numerical foundations

Validation approach: adapter checks, integration tests, and regression comparisons.

### Custom layers (full validation)
- TOML schema and loading
- Notebook-to-TOML extraction and mapping
- Feature detection and backend dispatch
- `math_bridge` symbolic parsing and expression handling
- Explain/render output generation
- CLI workflows, logging, and error handling

## Practical implementation guidance
- Maintain a small, representative golden set of configs and expected outputs.
- Prefer parameterised tests for edge coverage.
- Add analytical checks where closed-form solutions exist.
- Keep notebook-driven and direct-TOML paths behaviourally consistent.
- Document assumptions and trust boundaries in `docs/validation_strategy.md`.

## Workflow expectations
- Each meaningful PR should include tests appropriate to the risk level of its changes.
- Validation docs should be updated when trust boundaries or workflow semantics change.
- Blog updates in `docs/blog/` should note what validation strategy was used and why.
