# 08 — Notebook Convergence Diagnostics and UX Refinements
## What we implemented
- Upgraded the marimo pricing workbook output from plain bullet lists to clearer structured summaries.
- Added runtime profile controls for interactive use:
  - `fast`,
  - `balanced`,
  - `accurate`.
- Added optional convergence diagnostics for vanilla routes:
  - price vs time-step resolution,
  - price vs mesh size (`ΔS`),
  - absolute error trend (log scale), including backend spread/difference context.
- Split a large notebook execution block into smaller, focused marimo cells (inputs, compute, summaries, plots, final assembly).
- Added workbook narrative sections explaining:
  - what the workbook does,
  - why it exists,
  - how to use it effectively.

## Key design decisions
- Keep heavy numerical logic in `src/pdealchemy/notebook_support.py` and keep notebook cells orchestration-focused.
- Treat convergence diagnostics as opt-in to avoid slowing default exploratory workflows.
- Expose mesh-size explicitly in convergence outputs so users can reason about numerical behaviour in physically meaningful terms, not only raw grid counts.
- Make runtime profile selection first-class to support fast iteration followed by accurate final runs.

## Validation approach
- Extended notebook support tests to assert convergence outputs, including mesh-size series.
- Preserved notebook export smoke coverage to catch marimo execution and dependency-graph issues.
- Ran notebook checks and full project quality gate after refactor to confirm no regressions.

## Usage snapshot
- `just notebook`
- `uv run pytest tests/test_notebook_support.py tests/examples/test_notebook_export.py`
- `just notebook-check`

## Lessons learned
- marimo cell graph constraints reward small, single-purpose cells and unique local variable naming.
- Convergence charts are more actionable when both discretisation controls (time steps and mesh size) are visible.
- Lightweight narrative guidance inside the workbook reduces onboarding friction and improves reproducibility for collaborators.
