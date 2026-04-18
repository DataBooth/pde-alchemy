# PDEAlchemy — Framework overview
## Project name and tagline
**PDEAlchemy** — Turning mathematical descriptions into accurate option prices with best-of-breed PDE solvers.
Python package: `pdealchemy`

## Core goals
- Build a lightweight, extensible Python framework for pricing vanilla and exotic options using discretised PDE methods.
- Minimise custom numerical code by leaning on mature libraries (`QuantLib-Python`, `py-pde`) and focusing custom effort on orchestration, validation, and explainability.
- Keep correctness first: rigorous validation, clear diagnostics, and explicit assumptions.

## Interfaces
1. Primary: CLI (`pdealchemy price`, `validate`, `explain`, `notebook-to-toml`)
2. Interactive: marimo notebooks for exploration and specification authoring
3. Assistive (phase 2): LLM copilot workflows

## Notebook-first specification style
Notebooks are a first-class way to define pricing problems using semantic cell names that map to TOML sections.

### Cell naming conventions
- `instrument()` → `[instrument]`
- `numeraire()` → `[numeraire]`
- `sde()` → `[mathematics.sde]`
- `pde()` → `[mathematics.operator]`
- `payoff()` → `[payoff]`
- `boundary_lower()`, `boundary_upper()` → `[boundary.lower]`, `[boundary.upper]`
- `discretisation()` → `[numerics]`
- `data_rates()`, `data_volatility()`, etc. → `[data.*]`

### Notebook helper conventions
- Function docstring: concise human description
- `mo.md(...)`: explanatory text or labels
- `math_eq(...)`: inline LaTeX or equation-library file reference
- `spec_md(...)`: markdown-file-backed narrative content for non-equation sections

### Canonical paths
- Template notebook: `templates/spec_template.py`
- Example notebook: `examples/notebooks/spec_black_scholes.py`
- Equation library root: `library/`

## Library structure
`library/` is organised by specification role:
- `library/pde/`
- `library/sde/`
- `library/payoff/`
- `library/boundary/`
- `library/discretisation/`
- `library/numeraire/`
- `library/data/`

## Development workflow
- Use granular, focused PRs into `main`.
- Keep `main` in a working state (tests passing, examples runnable).
- After meaningful merges, add short engineering notes in `docs/blog/`.
- Prefer `just` recipes for repeatable local workflows.

## Validation philosophy
Validation is risk-based and progressive:
1. Unit tests on custom orchestration logic
2. Analytical benchmarks
3. Convergence studies
4. Monte Carlo cross-checks
5. Regression golden-set tests

Canonical validation guidance lives in `VALIDATION_PHILOSOPHY.md` and `docs/validation_strategy.md`.

## Error handling and logging
- Use `PDEAlchemyError` subclasses with actionable suggestions.
- Keep CLI output clear and structured.
- Support debug and verbose logging paths (`--debug`, `--verbose`).

## Guidance for contributors and assistants
- Keep changes small, explicit, and test-backed.
- Prioritise correctness, transparency, and maintainability over premature optimisation.
- Ensure notebook-driven and TOML-driven flows stay consistent.
