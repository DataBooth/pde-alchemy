# PDEAlchemy — Validation Philosophy

## Purpose
This document defines how we approach validation and testing in PDEAlchemy to achieve high correctness with **minimal redundant effort**.

The goal is to focus testing resources on the parts we actually control (the orchestration layer) while intelligently leveraging the maturity and pre-existing validation of the underlying best-of-breed libraries.

## Core Validation Principles

1. **Trust but Strategically Verify**
   - Heavily used, battle-tested libraries (especially QuantLib-Python) are treated as **pre-validated components**.
   - We do not re-implement or exhaustively test the numerical core of these libraries.
   - Our validation effort is concentrated on the glue code, configuration handling, feature detection, dispatching logic, adapters, symbolic math bridge, and end-to-end behavior.

2. **Risk-Based Testing**
   - Highest scrutiny on novel or custom code (config parsing, dispatcher, math_bridge, render/explain).
   - Medium scrutiny on thin adapters that connect to pre-validated libraries.
   - Lower scrutiny (smoke + integration tests only) on paths that delegate directly to QuantLib FD engines or py-pde core.

3. **Progressive Validation Pyramid**
   - Start simple and build complexity.
   - Every new feature must pass the entire pyramid before being considered stable.
   - Analytical cases first → convergence → Monte Carlo cross-checks → exotic combinations.

4. **Transparency & Visibility**
   - Maintain clear documentation of what is pre-validated vs. what is newly tested.
   - Use code coverage tools to show coverage of *our* orchestration code.
   - Explicitly mark tests that rely on pre-validated components.

## Component Classification

### Pre-Validated / Trusted Layers (Minimal Re-Testing)
- **QuantLib-Python**:
  - FD engines (`FdBlackScholesVanillaEngine`, `FdBlackScholesAsianEngine`, `FdBarrierEngine`, etc.)
  - Stochastic processes and basic payoff/exercise classes
  - Step conditions and discrete event handling
- **py-pde** core (grid management, time-stepping, basic operator evaluation)
- **SymPy** symbolic parsing and lambdify
- **NumPy / SciPy** basic numerics and linear algebra

**Validation approach for these layers**: Smoke tests + correct adapter usage + end-to-end golden-set regression. Rely on the libraries’ own extensive test suites and industry usage.

### Custom Layers Requiring Full Validation
- TOML schema and `pydantic-settings` models
- Feature detection and dispatcher logic
- `math_bridge` (symbolic string → callable, dimension inference, operator construction)
- `render/` module (explain command — accurate mathematical description generation)
- Adapter logic (custom step conditions, discrete events, auxiliary SDEs)
- Overall pricing pipeline and error handling paths
- Logging and CLI output

### End-to-End Integration
- Golden-set regression suite (known-good TOML configs + expected prices / rendered descriptions)
- Convergence order verification (framework controls grid and scheme)
- Monte Carlo cross-validation for path-dependent and exotic features
- Stress testing (edge parameters, high dimensions, stability)

## Practical Implementation Guidelines

- **Golden-Set Regression**: Small set of canonical TOML files with known-good outputs. Run on every PR.
- **Parameterized & Property-Based Testing**: Cover wide parameter ranges efficiently.
- **Test Markers**: Use pytest markers to clearly indicate reliance on pre-validated components, e.g.:
  ```python
  @pytest.mark.prevalidated("quantlib")
  def test_asian_adapter()
Coverage Reporting: Focus coverage metrics on orchestration modules (config/, core/, math_bridge/, render/). Exclude or de-emphasize thin wrappers.
ValidationRunner: A central class that supports different depths (quick, full, exotic) to balance speed and thoroughness during development vs. CI.
Documentation: Maintain docs/validation_strategy.md with a living "Trust Matrix" showing routing decisions (QuantLib vs. py-pde vs. custom).

Integration with Development Workflow

Each granular PR must include appropriate tests and update the validation strategy if new components are introduced.
Blog posts after each PR should explicitly discuss the validation approach taken for that step (e.g., “Leveraged QuantLib’s tested FD engine; added X unit tests for our symbolic parser and dispatcher”).
Coverage reports should be generated in CI and included in PR descriptions.

Success Criteria

High confidence in correctness without excessive test maintenance burden.
Clear visibility for developers and users: “80% of numerical heavy lifting is covered by pre-validated libraries; our tests focus on the orchestration and integration layers.”
Fast feedback loop during development (quick validation mode) while maintaining rigor for releases.


Usage Instructions for LLMs / Developers
When proposing code or new features for PDEAlchemy:

Always consider which validation layer the change belongs to.
Prefer leveraging pre-validated components where possible.
Include appropriate tests (unit for custom logic, integration/golden-set for end-to-end).
Update this philosophy document or validation_strategy.md if the classification changes.
In blog posts, clearly explain the validation strategy used for that increment.

This approach ensures we build a correct, maintainable framework efficiently.