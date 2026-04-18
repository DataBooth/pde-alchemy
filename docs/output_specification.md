# Output specification
This document defines expected output artefacts, content, and format options for the Black-Scholes notebook-first workflow.

## Scope
The current specification focuses on the canonical Black-Scholes baseline path:
- source notebook: `examples/notebooks/spec_black_scholes.py`
- blueprint TOML: generated via `notebook-to-toml`
- pricing TOML: generated via `spec-to-runtime-toml`

## Core artefacts
Each run should produce, or be able to produce, the following artefacts.

### 1) Specification artefact
- **Artefact**: blueprint TOML
- **Purpose**: semantic representation of the notebook specification
- **Minimum content**:
  - metadata title
  - instrument summary
  - SDE/PDE references
  - payoff/boundary references
  - discretisation reference
  - rate/volatility references

### 2) Runtime artefact
- **Artefact**: pricing TOML
- **Purpose**: executable schema-conformant config for `validate`, `price`, and `explain`
- **Minimum content**:
  - `[process]` with state variables, parameters, drift, diffusion
  - `[instrument]` with payoff, maturity, exercise, style
  - `[numerics]` and `[numerics.grid]`

### 3) Validation artefact
- **Artefact**: validation summary
- **Purpose**: quality gate outcome for schema and constrained equation checks
- **Minimum content**:
  - pass/fail status
  - backend used
  - equation-library summary (files + equations)
  - analytical benchmark result where enabled

### 4) Pricing artefact
- **Artefact**: pricing result
- **Purpose**: reproducible numeric output for the runtime config
- **Minimum content**:
  - price value
  - backend
  - engine identifier

### 5) Explain artefact
- **Artefact**: explain output
- **Purpose**: human-readable model and PDE summary
- **Minimum content**:
  - instrument and process summary
  - SDE and PDE text
  - terminal condition
  - solver settings summary

### 6) Notebook reporting artefact
- **Artefact**: configurable notebook report
- **Purpose**: analyst-facing output selection for pricing and sensitivities
- **Minimum content**:
  - selectable sections (`pricing`, `sensitivities`, `spot sweep`, `convergence`, `validation`, `explain`)
  - selectable render modes (`tables`, `Plotly charts`, or both)
  - backend-comparison support for vanilla routes

### 7) Combined notebook artefact
- **Artefact**: specification-plus-report notebook
- **Purpose**: maintain one notebook that presents spec content first, then outputs
- **Notebook**: `examples/notebooks/spec_black_scholes_with_results.py`
- **Minimum content**:
  - full semantic specification section (instrument, assumptions, SDE/PDE, payoff/boundary, data references)
  - reporting controls and output sections appended below the specification

## Format options
Recommended output formats:

1. **Terminal text** (default)
- Best for local iterative use and CI logs.

2. **Markdown**
- Best for notebooks, PR summaries, and research notes.

3. **JSON**
- Best for machine processing and downstream tooling.

4. **CSV**
- Best for tabular summaries and lightweight BI usage.

5. **Excel (`.xlsx`)**
- Best for analyst review, handoff, and workbook-based comparison.
- Suggested workbook layout:
  - `summary`
  - `validation`
  - `pricing`
  - `explain`
  - `metadata`

## Notebook options
- Results notebook only: `examples/notebooks/black_scholes_results.py`
- Combined spec + outputs notebook: `examples/notebooks/spec_black_scholes_with_results.py`

## Baseline command chain
```bash
uv run pdealchemy notebook-to-toml examples/notebooks/spec_black_scholes.py --output examples/notebooks/black_scholes_blueprint.toml --overwrite
uv run pdealchemy spec-to-runtime-toml examples/notebooks/black_scholes_blueprint.toml --output examples/notebooks/black_scholes_pricing.toml --overwrite
uv run pdealchemy validate examples/notebooks/black_scholes_pricing.toml --equation-library library
uv run pdealchemy validate examples/notebooks/black_scholes_pricing.toml --analytical --tolerance 0.75
uv run pdealchemy price examples/notebooks/black_scholes_pricing.toml
uv run pdealchemy explain examples/notebooks/black_scholes_pricing.toml --format markdown
```
