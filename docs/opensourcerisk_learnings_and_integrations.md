# OpenSourceRisk (ORE): Potential Learnings and Integration Paths for PDEAlchemy
## Purpose
This note captures practical learnings and realistic integration options between PDEAlchemy and OpenSourceRisk (ORE), based on current public documentation and repositories:

- `https://github.com/OpenSourceRisk/Engine`
- `https://opensourcerisk.org`
- `https://github.com/OpenSourceRisk/ORE-SWIG`

The aim is to identify where ORE can improve PDEAlchemy’s correctness, transparency, and extensibility without overcommitting to unnecessary complexity.

## Relevant ORE Snapshot
From ORE’s public material, the most relevant points for PDEAlchemy are:

- ORE is positioned as a transparent, peer-reviewed framework for pricing and risk analysis, built on QuantLib.
- ORE’s core stack is C++ and is described as three libraries: QuantExt, OREData, and OREAnalytics, plus command-line application workflows.
- ORE supports structured interfaces for trade data, market data, and system configuration (notably API/XML-driven workflows).
- Documentation depth is substantial (user guide, product catalogue, methods, design notes, and supplementary documents).
- ORE includes broad risk analytics scope (e.g., exposure, XVA, stress/risk workflows), plus a large set of examples and tests.
- ORE-SWIG provides language bindings (including Python), which introduces an integration path for Python-first projects.

## Why ORE Is Relevant to PDEAlchemy
PDEAlchemy currently focuses on:

- transparent TOML-driven pricing workflows,
- CLI and notebook usability,
- backend dispatch between QuantLib and `py_pde`,
- practical validation strategies and reproducibility.

ORE is relevant because it can act as:

- a **benchmark reference** for pricing/risk behaviours in overlapping product areas,
- a **design reference** for configuration and model governance at scale,
- a **future expansion signal** if PDEAlchemy broadens beyond pricing into richer risk analytics.

## Potential Learnings (Without Any Direct Integration)
These are high-value learnings that can be adopted independently of linking to ORE binaries/libraries.

### 1) Configuration Separation at Scale
ORE’s separation of product description, market data, and analytics setup suggests a useful pattern:

- keep instrument intent separate from numerical method choices,
- keep market data contracts explicit and versioned,
- keep analytics/reporting configuration orthogonal to pricing config.

Potential PDEAlchemy action:
- evolve TOML schema into clearly separated sections with stronger schema-level cross-checks.

### 2) Explicit Capability Contracts
ORE’s broad product/method catalogue highlights the importance of machine-readable capability boundaries.

Potential PDEAlchemy action:
- maintain backend capability metadata (supported products, features, numerics, and constraints),
- enforce early validation errors before runtime dispatch.

### 3) Example-Centred Validation Discipline
ORE’s extensive examples and documentation indicate a mature “examples as contracts” practice.

Potential PDEAlchemy action:
- grow canonical example coverage for each major feature slice,
- treat examples as regression artefacts with expected numeric tolerances and diagnostics.

### 4) Method and Assumption Transparency
ORE’s methods documentation is a strong reminder that trust requires visible assumptions and model boundaries.

Potential PDEAlchemy action:
- extend explain output to include numerical assumptions, stability caveats, and product-specific limitations.

### 5) Separation of Core Engine vs Integration Surfaces
ORE demonstrates that user-facing integrations (CLI, notebooks, APIs) can evolve without destabilising core analytics.

Potential PDEAlchemy action:
- keep adapter and interface seams strict so notebook/CLI changes do not leak into solver internals.

## Integration Options
The options below are ordered from lowest to highest coupling.

### Option A: Benchmark-Only Integration (Recommended First)
Use ORE as an external reference engine for overlapping instruments and scenarios.

What to implement:
- curated benchmark scenarios where PDEAlchemy and ORE should be directionally or numerically comparable,
- automated comparison runner producing error metrics and tolerance checks,
- reproducible fixture snapshots (inputs + expected outputs + metadata).

Pros:
- low coupling,
- immediate validation value,
- avoids build-chain complexity in the first stage.

Cons:
- no runtime feature reuse,
- requires careful mapping of conventions.

### Option B: TOML → ORE Input Translation Layer
Build a translator from PDEAlchemy TOML configs into ORE-compatible input structures (initially for a narrow instrument subset).

What to implement:
- canonical mapping spec for day count, calendars, conventions, and curves/surfaces,
- deterministic translator with schema-level diagnostics,
- round-trip tests on a selected vanilla subset.

Pros:
- stronger apples-to-apples comparisons,
- creates a formal semantic contract across systems.

Cons:
- medium complexity,
- drift risk when either schema evolves.

### Option C: Process-Level ORE Adapter
Treat ORE as an external executable/service called by PDEAlchemy when explicitly selected.

What to implement:
- adapter that writes input files, invokes ORE, parses outputs,
- clear error surfaces for configuration mismatches,
- timeout/retry and logging strategy.

Pros:
- language/runtime isolation,
- avoids in-process C++ binding friction.

Cons:
- operational overhead,
- slower than in-process paths,
- requires robust output parsing contracts.

### Option D: In-Process Python Binding Integration (ORE-SWIG)
Use ORE-SWIG bindings directly from Python for tighter coupling.

What to implement:
- environment/build playbooks per platform,
- compatibility matrix for Python/ORE/QuantLib versions,
- adapter tests for deterministic behaviour.

Pros:
- potentially cleaner runtime integration once stable.

Cons:
- highest maintenance burden,
- toolchain complexity,
- versioning and ABI compatibility risk.

## Recommended Roadmap for PDEAlchemy
### Phase 0: Discovery and Contract Definition
- define a minimal overlap set (e.g., vanilla European options with known market conventions),
- document input normalisation rules and expected tolerances,
- confirm licensing and redistribution obligations for any packaged artefacts.

### Phase 1: External Benchmark Harness
- implement benchmark runner and result schema,
- add CI-safe fixtures (no live market dependencies),
- publish benchmark interpretation guidance in docs.

### Phase 2: Translation Pilot
- implement TOML→ORE translation for one narrow flow,
- add mismatch diagnostics and semantic validation checks,
- run controlled comparisons in notebook and CLI outputs.

### Phase 3: Decide Runtime Integration Strategy
- if benchmark and translation value is high, choose process adapter first,
- only consider in-process bindings after proving sustained demand and maintenance capacity.

## Key Risks and Mitigations
### Risk: Semantic mismatches in conventions
Mitigation:
- formal mapping spec,
- explicit convention snapshots in fixtures,
- strict validation errors on ambiguous mappings.

### Risk: Build and operational complexity
Mitigation:
- prefer benchmark/process integration before binding-level coupling,
- keep platform-specific setup isolated from core workflows.

### Risk: False confidence from near-matches
Mitigation:
- compare not only price, but also diagnostics and sensitivity trends where feasible,
- require tolerance rationale per product and method.

### Risk: Licence and packaging ambiguity
Mitigation:
- verify exact licence terms and notices at integration time,
- keep third-party artefacts and attribution requirements documented.

## Concrete Backlog Candidates
- Add `ore_benchmark` workflow for a small vanilla scenario set.
- Define a `convention_mapping.md` note for day count, calendars, and vol/curve assumptions.
- Introduce result-comparison artefacts (absolute error, relative error, tolerance status, metadata).
- Add one notebook view that overlays PDEAlchemy vs external reference prices for selected scenarios.
- Add a “reference engine provenance” field to validation output for auditability.

## Non-Goals (for Now)
- Full ORE product coverage.
- Immediate XVA/risk-stack parity.
- Tight in-process binding integration without prior benchmark evidence.

## References
- OpenSourceRisk Engine repository: `https://github.com/OpenSourceRisk/Engine`
- OpenSourceRisk main site: `https://opensourcerisk.org`
- ORE documentation portal: `https://www.opensourcerisk.org/documentation/`
- ORE Doxygen (OREAnalytics intro): `https://www.opensourcerisk.org/docs/orea/index.html`
- ORE-SWIG repository: `https://github.com/OpenSourceRisk/ORE-SWIG`
