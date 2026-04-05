# 04 — Canonical Examples and Documentation Pass
## What we implemented
- Canonical TOML examples for vanilla and exotic pricing.
- README quick-start and CLI usage refinements.
- Better first-run guidance for contributors and users.

## Key design decisions
- Keep examples canonical and representative rather than exhaustive.
- Prefer examples that align directly with validation and regression tests.
- Make default developer workflows visible and minimal.

## Validation approach
- Example-driven integration checks to ensure configs remain executable.
- Regression-style tests around canonical files to catch behavioural drift.
- Documentation updates tied to commands verified in local checks.

## Usage snapshot
- `just check`
- `uv run pdealchemy price examples/vanilla_european_call.toml`

## Lessons learned
- Canonical examples are both user documentation and test fixtures.
- Tight coupling between docs and executable checks reduces documentation rot.
