# Market Data Sources
This document defines which market data sources are suitable for PDEAlchemy, why they are used, and where their use is intentionally limited.

## Core Principles
- Pricing and validation must remain deterministic and reproducible.
- Unit and integration tests must not depend on live external APIs.
- Live data connectors are ingestion helpers, not pricing dependencies.
- Source licensing and redistribution constraints must be respected.

## Approved Source Categories
### 1) Official rate sources (preferred for curve fixtures)
Examples:
- U.S. Treasury daily yield data.
- Other official public yield publications with clear licensing.

Purpose:
- Build realistic risk-free and dividend curve fixtures.
- Provide reference snapshots for regression testing.

Limits:
- Do not query these endpoints during tests.
- Snapshot once, normalise, and store fixture extracts locally.

### 2) Open options datasets (surface fixture seeding)
Examples:
- Publicly licensed options-chain datasets with implied volatility fields.

Purpose:
- Seed representative volatility surface fixtures.
- Test market surface mapping into QuantLib structures.

Limits:
- Treat as research-grade fixture input, not guaranteed production quality.
- Preserve provenance metadata and licence notes in ingestion scripts/docs.

### 3) Public exchange APIs (optional ingestion)
Examples:
- Exchange public endpoints that expose options quotes and implied volatility.

Purpose:
- Support ad hoc ingestion and exploratory workflows.
- Refresh internal snapshots when explicitly requested.

Limits:
- Network availability, rate limits, and schema drift make these unsuitable for test execution.
- Any ingested dataset must be materialised into DuckDB and versioned by `as_of` date before use.

### 4) Convenience aggregators (experimental)
Examples:
- `yfinance`, `yahooquery`, OpenBB connectors.

Purpose:
- Rapid prototyping and exploratory data pulls.

Limits:
- Not authoritative pricing sources.
- Not suitable as mandatory runtime dependencies for validation-critical flows.
- Must not be called directly in automated tests.

## DuckDB Normalisation Contract
All external source data should be normalised into standard tables before pricing use.

Minimum recommended tables:
- `curve_nodes(curve_id, as_of, t_years, zero_rate, currency, source)`
- `vol_surface_points(surface_id, as_of, t_years, strike, implied_vol, source)`

This contract keeps adapters source-agnostic and ensures reproducible snapshots.

## Testing Policy
- Tests consume only local fixture snapshots.
- Fixture generation scripts may use live sources, but are run manually.
- Every fixture should include:
  - source identifier,
  - snapshot date (`as_of`),
  - transformation notes.

## Out of Scope (for now)
- Real-time production market data service guarantees.
- Automatic entitlement/licence handling.
- Full Bloomberg-equivalent coverage.
