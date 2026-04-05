# 05 — marimo Notebook Explorer
## What we implemented
- Notebook support helpers for canonical config loading and reusable output generation.
- Interactive marimo explorer at `examples/notebooks/price_explorer.py`.
- Notebook-focused workflow recipes and README instructions.

## Key design decisions
- Keep notebook logic thin by centralising orchestration helpers in package code.
- Reuse canonical examples to avoid divergence between CLI and notebook pathways.
- Treat notebook startup checks as first-class verification, not ad hoc manual testing.

## Validation approach
- Added tests for notebook support utilities.
- Added marimo static check workflow (`just notebook-check`).
- Performed notebook startup smoke checks and handled UI default selection edge cases.
- Kept numerical heavy lifting delegated to trusted libraries while testing notebook orchestration glue.

## Usage snapshot
- `just notebook`
- `just notebook-check`
- `just notebook-run`

## Lessons learned
- marimo UI defaults need careful key/value handling to avoid runtime surprises.
- Reusing existing orchestration modules keeps interactive tooling maintainable.
