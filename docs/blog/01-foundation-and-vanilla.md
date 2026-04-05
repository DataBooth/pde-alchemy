# 01 — Foundation and First Vanilla Flow
## What we implemented
- Initial package scaffold with `uv` dependency management.
- `just` task runner and baseline workflows.
- CLI shell with `price`, `validate`, and `explain` command structure.
- Error hierarchy and logging baseline.

## Key design decisions
- Keep the first increment intentionally narrow and production-safe.
- Prefer robust existing libraries over bespoke numerical implementations.
- Establish clean interfaces early so later solver and adapter work can remain focused.

## Validation approach
- Added unit tests for first-layer custom behaviour.
- Kept validation effort focused on orchestration and error handling.
- Used smoke checks for command wiring and baseline execution paths.

## Usage snapshot
- `uv sync --all-extras --dev`
- `just check`
- `uv run pdealchemy --help`

## Lessons learned
- A small, reliable first slice keeps later increments faster and safer.
- CLI ergonomics are easier to maintain when error formatting is treated as core behaviour, not an afterthought.
