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

## ADR-006 — Use separate NAV ingestion tables for events, current state and feed progress

### Status

Accepted

### Decision

The initial PostgreSQL ingestion model will use three separate tables:

- `nav_feed_events` for immutable, privacy-minimised source events
- `job_advertisements_current` for the latest known state of each advertisement
- `nav_feed_progress` for resumable polling and conditional-request metadata

Operational identifiers, statuses and timestamps will use typed columns.
Privacy-minimised source payloads will remain in JSONB until their live
structure and analytical requirements are verified.

The current-state table will reference its latest historical event using both
the event identifier and advertisement identifier.

### Reason

Historical events, current vacancy queries and feed recovery have different
storage and update requirements.

Separating them preserves source history, supports efficient current-state
queries and prevents feed progress from advancing independently of successful
event processing.

A composite relationship between current state and historical events prevents
an advertisement from referencing an event that belongs to another
advertisement.

### Consequences

- Historical source events are inserted rather than overwritten.
- Current advertisement rows may be updated as newer events are accepted.
- Feed progress must advance in the same transaction as successful event and
  current-state processing.
- Personal contact data must be removed before either JSONB payload is stored.
- Provisional source assumptions remain documented rather than enforced through
  unverified enums, triggers or complex analytical columns.
- The initial tables remain in PostgreSQL's `public` schema until a dedicated
  ingestion namespace is justified.

## ADR-007 — Keep the NAV HTTP client limited to one feed page

### Status

Accepted

### Decision

The initial NAV HTTP client will request and validate one feed page at a time.

Complete pagination, persistent progress tracking, database writes, scheduled
polling and orchestration will remain outside the client.

The client will disable automatic redirects and only send Bearer credentials
to URLs using the configured feed origin.

### Reason

A narrow client is easier to test, review and reuse without combining network,
privacy, database and orchestration responsibilities.

Same-origin enforcement and disabled redirects reduce the risk of forwarding
the NAV credential to an unexpected destination.

### Consequences

- Feed iteration will be implemented by a separate ingestion workflow.
- HTTP behaviour can be tested entirely through mocked transports.
- `next_url` values must be validated before later requests.
- Transport and response failures are translated into project exceptions.
- Database progress cannot advance inside the HTTP client.

## ADR-008 — Hash canonical payloads only after privacy minimisation

### Status

Accepted

### Decision

NAV advertisement payloads will be deep-copied and have their top-level
`contactList` removed before hashing or future persistence.

The minimised payload will be validated and serialized as canonical JSON using
sorted keys, compact separators and UTF-8 encoding. Its deterministic integrity
hash will use SHA-256.

### Reason

Hashing before privacy minimisation could create identifiers derived from data
that the project has explicitly decided not to retain.

Canonical serialization ensures that equivalent JSON objects produce the same
hash regardless of dictionary insertion order.

### Consequences

- Source objects are not mutated during minimisation.
- Payloads containing a top-level `contactList` cannot be hashed through the
  accepted hashing function.
- Non-JSON values and non-finite numbers are rejected.
- Equivalent minimised payloads produce the same deterministic hash.
- The hash supports integrity checking and diagnostics but is not currently the
  event uniqueness key.
- The source-event repository persists the calculated hash with the accepted
  privacy-minimised event.

## ADR-009 — Use a caller-owned Psycopg repository for source events

### Status

Accepted

### Decision

The source-event persistence boundary will use Psycopg 3 and parameterised SQL
to insert privacy-minimised events into `nav_feed_events`.

The repository will receive an existing database connection and will not commit,
roll back or close that connection.

Duplicate `source_event_id` values will use
`ON CONFLICT (source_event_id) DO NOTHING`. The repository will return a
structured duplicate result containing the existing internal event identifier
rather than treating an expected replay as an infrastructure failure.

The repository will not update `job_advertisements_current` or
`nav_feed_progress`.

### Reason

Caller-owned transactions allow later ingestion logic to compose source-event
insertion, current-state maintenance and feed-progress advancement into one
atomic unit.

Conflict-aware insertion preserves source-event immutability and supports
idempotent resumable processing without hiding unrelated database failures.

A narrow repository keeps HTTP, privacy, persistence and orchestration
responsibilities independently testable.

### Consequences

- `DATABASE_URL` is loaded only when database access is requested.
- Database credentials and complete payloads are excluded from public error
  messages.
- JSON payloads use Psycopg's JSONB adaptation.
- New source events return a generated internal event identifier.
- Repeated source events return the existing identifier without an update.
- Check-constraint and infrastructure failures remain visible as safe
  project-level persistence errors.
- The caller owns commit, rollback and connection closure.
- Current-state and feed-progress writes require later repository operations and
  an orchestration boundary.
- PostgreSQL integration tests run against an isolated temporary database.
