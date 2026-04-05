# Backlog
## Current outstanding items
- Complete the config-driven notebook selection refactor in `src/pdealchemy/notebook_support.py` and `examples/notebooks/price_explorer.py`.
- Finalise tests for the selection helpers (dropdown option generation and selection resolution) alongside the notebook export smoke test.
- Fix py-pde boundary condition wiring to remove deprecation warnings, e.g. `DeprecationWarning: Deprecated format for boundary conditions. Boundary conditions for each axis are set using a dictionary: {"x": bc_x, "y-": bc_y_lower, "y+": bc_y_upper}.`
- Re-run the full validation suite (`just notebook-check` and `just check`) to confirm all checks pass without interruption.
- Commit the hotfix branch changes, push to origin, and open a focused pull request for review.
- Profile notebook runtime and backend pricing performance (cell-level timing + backend call timing), then prioritise optimisations for long-running interactive calculations.

## Ideas from reviewing BlackScholesPINN
- Add an experimental PINN backend (research track) for 1D vanilla Black-Scholes as an optional solver path, clearly marked non-production.
- Introduce a config block for PINN experiments (network depth/width, epochs, learning rate, collocation count, random seed), similar to the repository’s `config.json` approach.
- Add explicit loss decomposition reporting (data-fit vs PDE-residual components) in training logs and notebook visualisations.
- Add synthetic data and collocation sampling utilities behind a deterministic seed to support reproducible PINN experiments.
- Add benchmark workflows comparing PINN outputs against analytical Black-Scholes and existing PDE backends (`quantlib`, `py_pde`) with error metrics and convergence plots.
- Add model artefact handling (`save`, `load`, inference-only path) for any future PINN training workflow.

## Potential benefits of these ideas
- Improve solver resilience by diversifying numerical approaches (PINN + finite-difference), reducing single-method risk.
- Enable faster research iteration through config-driven experiments without repeated code edits.
- Increase debugging clarity and model trust through decomposed loss diagnostics.
- Improve reproducibility and comparability with deterministic sampling and seeded runs.
- Support objective backend selection with shared error and convergence benchmarks.
- Create a path to reusable trained models for faster inference and lower repeated compute cost.

## Ideas from reviewing GPUEngineering/PDESolvers
- Add a PDE sandbox track (1D heat now, 2D heat later) to validate numerical infrastructure independently from option-pricing logic.
- Add an interpolation-based grid comparison utility (coarse vs fine) for solver cross-resolution error checks.
- Extend benchmarking outputs to structured artefacts (CSV + plots) for runtime, absolute error, and convergence trends.
- Add a reusable Monte Carlo convergence helper that benchmarks against analytical Black-Scholes references with fixed random seeds.
- Introduce a stable result object contract for all backends (solution grids, Greeks/diagnostics, timing metadata, and export hooks).
- Define an optional acceleration boundary for future GPU backends (adapter/plugin seam), while keeping Python paths first-class.
- Add capability metadata for each backend (supported instruments, dimensions, and numerical methods) to power notebook/UI guardrails.

## Potential benefits of PDESolvers-inspired ideas
- Improves correctness confidence by validating solver mechanics on simpler PDEs before adding financial complexity.
- Makes numerical quality easier to track over time with reproducible error and convergence artefacts.
- Strengthens regression detection when backend changes impact speed, stability, or pricing accuracy.
- Improves comparability between methods by standardising result payloads and benchmark outputs.
- Reduces integration risk if GPU acceleration is added later by defining clean backend boundaries early.
- Improves notebook/user experience through capability-aware controls that prevent invalid backend/method combinations.

## Ideas from paper metadata review (DOI: `10.1016/j.camwa.2025.04.003`)
- Add a finite-difference scheme plug-in seam for vanilla Black-Scholes PDE solves (e.g. explicit, Crank-Nicolson, and new candidate schemes) with a consistent solver interface.
- Add a numerical verification harness for PDE schemes covering stability, convergence rate, and boundary-condition sensitivity on canonical vanilla cases.
- Add no-arbitrage sanity checks to scheme outputs (non-negative price, monotonicity in spot, and basic convexity checks) as regression guards.
- Add a reproducible benchmark matrix (accuracy vs analytical Black-Scholes, runtime, and memory) across grid/time-step settings and schemes.
- Follow up with a full-paper review once access is available to capture exact discretisation details and any implementation-specific tricks.

## Potential benefits of paper-inspired ideas
- Gives a safer path to adopt improved PDE schemes without disrupting existing backends.
- Makes scheme trade-offs explicit (accuracy versus runtime) for both library defaults and notebook UX.
- Reduces risk of subtle numerical regressions by baking financial no-arbitrage checks into validation.
- Improves confidence when selecting default numerics for production-style pricing runs.
