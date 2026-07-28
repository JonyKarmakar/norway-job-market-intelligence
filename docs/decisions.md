# Architecture Decision Records

This document records important technical and scope decisions for the Norway Job Market Intelligence Platform.

## ADR-001 — Use the NAV pam-stilling-feed

### Status

Accepted

### Decision

The project will use the NAV `pam-stilling-feed` as its initial and only vacancy source for the local MVP.

The deprecated `pam-public-feed` will not be used.

### Reason

The stilling-feed is NAV's current official event-based vacancy feed and supports tracking advertisement updates and inactive states.

### Consequences

- The project must maintain its own advertisement state.
- Filtering and analytical classification must be implemented by the project.
- Feed pagination and polling progress must be persisted.
- Source limitations must be communicated clearly.

## ADR-002 — Separate source events from current advertisement state

### Status

Accepted

### Decision

Immutable source events will be retained separately from the latest clean state of each advertisement.

### Reason

A new feed entry can be generated whenever an advertisement changes. Historical events and current operational state serve different purposes.

### Consequences

- The ingestion layer must support append-only event storage.
- The current-state table must support idempotent updates.
- Advertisement UUIDs and feed-event identifiers must be modelled separately.
- Historical events can support replay, auditing and debugging.

## ADR-003 — Exclude personal contact data from persistent and analytical use

### Status

Accepted

### Decision

The source `contactList`, including names, email addresses, telephone numbers, roles and titles, will be removed before persistent storage.

Personal contact data will not be included in analytical models, dashboards, API responses, logs, test fixtures or AI retrieval.

### Reason

These fields are unnecessary for labour-market analysis and would increase privacy and retention risk.

### Consequences

- Privacy minimisation must occur before writing source payloads to PostgreSQL.
- The ingestion layer must record that minimisation was applied.
- Test fixtures must use redacted or synthetic contact data.
- Raw event records will be immutable after privacy minimisation.

## ADR-004 — Build the local MVP before a cloud extension

### Status

Accepted

### Decision

PostgreSQL, dbt, Prefect, FastAPI, Power BI and Docker Compose will form the core local system.

Microsoft Fabric, Copilot Studio or Power Automate will be introduced only after the local MVP is stable.

### Reason

The portfolio must demonstrate a complete end-to-end system without depending on temporary cloud access.

### Consequences

- Local development and reproducibility take priority.
- Cloud-specific architecture will not control the core design.
- Only one focused Microsoft ecosystem extension will be added later.

## ADR-005 — Publish explicit market-coverage limitations

### Status

Accepted

### Decision

All analytical outputs will state that the platform represents vacancies observed through NAV's feed rather than the complete Norwegian job market.

The project will not claim full vacancy coverage.

### Reason

NAV does not receive every publicly advertised vacancy, and FINN.no advertisements are excluded.

### Consequences

- Dashboard and API documentation must include the coverage limitation.
- Analytical conclusions must be described as dataset observations.
- Comparisons and trends must not be presented as complete national-market measurements.
