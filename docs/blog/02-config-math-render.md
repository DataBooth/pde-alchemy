# 02 — Config Models, Symbolic Bridge, and Explain Render
## What we implemented
- Pydantic config schema and TOML loading path.
- Symbolic parsing and model-to-maths bridge with SymPy.
- `explain` rendering for readable mathematical and textual outputs.

## Key design decisions
- Use strongly validated schema boundaries to prevent late-stage pricing failures.
- Keep symbolic parsing isolated from CLI concerns.
- Treat explain output as a first-class product feature for transparency.

## Validation approach
- Unit tests on custom schema, parsing, and render behaviour.
- Focused assertions on deterministic explain output structure.
- Relied on SymPy’s pre-validated symbolic engine while validating our orchestration around it.

## Usage snapshot
- `uv run pdealchemy explain examples/vanilla_european_call.toml --format markdown`

## Lessons learned
- Clean validation errors in config loading save significant debugging time.
- Small renderer-focused tests prevent regressions in user-facing mathematical descriptions.
