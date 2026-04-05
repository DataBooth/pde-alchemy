# 06 — Convenience Workflow Recipes
## What we implemented
- Added dedicated `just` recipes for `price`, `validate`, and `explain`.
- Added `notebook-check` recipe for fast notebook validation.
- Clarified `notebook-run` interrupt behaviour in README.

## Key design decisions
- Make common tasks explicit to reduce command friction.
- Keep defaults aligned with canonical examples for predictable first runs.
- Document expected long-running server exit semantics so users can distinguish normal interrupts from errors.

## Validation approach
- Confirmed recipe availability via `just --list`.
- Verified notebook structure with `just notebook-check`.
- Ran full suite with `just check` after recipe updates.

## Usage snapshot
- `just price`
- `just validate`
- `just explain`
- `just notebook-check`

## Lessons learned
- Small workflow affordances can materially improve day-to-day development speed.
- Explicit command recipes reduce ambiguity for contributors and automation.
