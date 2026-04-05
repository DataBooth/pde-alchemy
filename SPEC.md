# PDEAlchemy — Framework Overview for LLM Assistants

## Project Name & Tagline
**PDEAlchemy** — Turning mathematical descriptions into accurate option prices with best-of-breed PDE solvers.

**Python package**: `pdealchemy`

## Project Goal
Build a lightweight, extensible Python framework for pricing general (including exotic/unusual) financial options using discretized PDE methods.

Minimize custom code by leveraging mature open-source libraries. Users define instruments via TOML config and stay close to the underlying mathematics (symbolic drift/diffusion/payoff expressions).

Prioritize **correctness first** (rigorous validation pyramid) over speed. Optimization (e.g., Mojo kernels) comes later.

## Development Workflow
- **Granular PR-driven process**: Each small, focused feature or step is developed in its own branch and merged via Pull Request to `main`.
- `main` branch is always kept in a working state (tests passing, basic examples runnable).
- **Progressive blogging**: After each meaningful PR is merged, a short blog post (Markdown) is written documenting:
  - What was implemented
  - Key design decisions
  - Lessons learned
  - Usage examples or screenshots
- This creates a living development blog series that documents the evolution of PDEAlchemy.

## User-Facing Interfaces
1. **Primary: CLI** (Typer + Rich) — production-ready, scriptable.
   - Commands: `price`, `validate`, `explain`
2. **Interactive/Exploratory: marimo notebooks** (optional examples)
3. **Assistive (Phase 2): LLM Copilot**

## Key Feature: Explain / Render Command
`pdealchemy explain config.toml [--format markdown|text|latex]`

Renders TOML into clean mathematical + textual description (SDEs, PDE, payoff, discrete conditions, boundaries, numerical setup).

## Library Stack
- **Config & Settings**: `pydantic` + `pydantic-settings`
- **CLI**: `typer` (with Rich)
- **Logging**: `loguru` (structured, contextual, multiple sinks)
- **Paths**: `pathlib`
- **Task Runner**: `just` (via `justfile`)
- **Core Solvers**: `QuantLib-Python`, `py-pde`
- **Math Bridge**: `SymPy` + `Numba`
- **Numerics**: `numpy`, `scipy`
- **Testing**: `pytest`
- **Interactive**: `marimo` (optional)
- Optional: `rich`, `matplotlib`/`plotly`

## High-Level Code Design
- `config/` — Pydantic models + settings
- `math_bridge/` — Symbolic parsing + renderer
- `render/` — Mathematical description generation
- `core/` — Builder, dispatcher, adapters
- `validation/` — Validation pyramid
- `cli/` — Typer commands
- `logging_config.py`, `exceptions.py` — Logging + error handling
- `examples/notebooks/` — marimo examples
- Blog posts in `docs/blog/` (progressive series)

## Error Handling & Logging
- Custom `PDEAlchemyError` hierarchy with clear messages and suggestions.
- Pydantic errors reformatted helpfully.
- Loguru with rich context, console + optional JSON sinks.
- Pretty Rich errors in CLI, detailed logging for debugging.
- `--debug` / `--verbose` flags.

## Validation Strategy
Progressive pyramid:
1. Unit tests
2. Analytical benchmarks
3. Convergence studies
4. Monte Carlo cross-checks
5. Regression golden-set tests

## LLM Copilot (Phase 2)
Natural-language assistance for config creation, explanations, and error help.

## marimo Notebooks (Optional)
Reactive interactive interface for exploration and demos.

## Next Steps (Granular PR Plan)
Development will proceed in small, mergeable steps via PRs to `main`, each followed by a blog post:

1. Project skeleton + pyproject.toml + justfile + basic logging & exceptions
2. Pydantic settings models + TOML schema
3. Math bridge + symbolic parser
4. Render/explain command + mathematical description output
5. Core dispatcher + QuantLib adapter
6. Validation harness (starting with analytical cases)
7. First exotic example (discrete Asian + barrier + dividend)
8. marimo notebook examples
9. Phase 2: LLM Copilot

---

**Instructions for LLM Assistants**  
Follow the granular PR + progressive blogging workflow. Keep changes small and focused. After each major step, suggest a blog post title and outline. Prioritize minimal custom code, excellent error handling/logging, CLI-first design, and the explain renderer.