# 03 — Pricing Core, Validation Harness, and Exotic Routing
## What we implemented
- Core dispatcher and QuantLib-backed pricing adapter wiring.
- Analytical benchmark runner for vanilla Black-Scholes comparison.
- Initial exotic support for discrete Asian, barrier, and dividend combinations.

## Key design decisions
- Route to pre-validated QuantLib engines instead of re-creating numerical internals.
- Keep feature detection and dispatch orchestration explicit and testable.
- Build validation harnesses that can scale in depth as feature complexity grows.

## Validation approach
- Strong test coverage on dispatcher and adapter selection logic.
- Analytical validation checks for deterministic vanilla confidence.
- Integration tests for exotic orchestration pathways with realistic configs.
- Trust-heavy numerical correctness to QuantLib, while deeply testing PDEAlchemy-owned control flow.

## Usage snapshot
- `uv run pdealchemy validate examples/vanilla_european_call.toml --analytical --tolerance 0.75`
- `uv run pdealchemy price examples/exotic_discrete_asian_barrier_dividend.toml`

## Lessons learned
- Separating routing logic from numerical engines keeps risk concentrated and testable.
- Analytical baselines are a practical anchor before broadening exotic combinations.
