# Current Advertisement-State Repository

## Purpose

The current advertisement-state repository maintains one latest accepted state
for each NAV advertisement in `job_advertisements_current`.

It works with source events that have already been stored immutably in
`nav_feed_events`.

The repository does not fetch NAV data, remove contact information, calculate
payload hashes, insert source events, update feed progress or commit the
caller's transaction.

## Processing position

The intended ingestion sequence is:

1. Fetch and validate one NAV feed page.
2. Remove the top-level `contactList`.
3. Validate the privacy-minimised payload.
4. Calculate the deterministic payload hash.
5. Insert the immutable source event.
6. Maintain the current advertisement state.
7. Advance feed progress after the complete transaction succeeds.

This milestone implements step 6.

## Public operation

The repository exposes:

`maintain_current_advertisement(connection, advertisement)`

The caller supplies:

- an existing Psycopg connection
- the advertisement source identifier
- the internal identifier of an already-persisted candidate event

The repository does not accept duplicate status, timestamp or payload values
from the caller.

Instead, it loads the following values from the immutable source event:

- `source_status`
- `source_updated_at`
- `ingested_at`
- `payload`

This prevents the current-state row from being populated with values that
disagree with its referenced historical event.

## Typed input

`CurrentAdvertisementInput` contains:

| Field | Purpose |
|---|---|
| `source_job_id` | Advertisement identifier whose current state is evaluated |
| `candidate_event_id` | Internal identifier of the stored candidate event |

The candidate event must exist and belong to the supplied advertisement.

## Typed result

`CurrentAdvertisementResult` contains:

| Field | Purpose |
|---|---|
| `source_job_id` | Evaluated advertisement identifier |
| `candidate_event_id` | Candidate historical event |
| `current_event_id` | Event representing current state after evaluation |
| `operation` | Meaningful repository outcome |
| `current_source_updated_at` | Current state's source timestamp after evaluation |

The `changed` property is true only for `CREATED` and `UPDATED`.

## Repository outcomes

### `CREATED`

Returned when no current-state row exists.

The repository:

- inserts one current-state row
- references the candidate source event
- copies status, source timestamp and payload from that event
- sets `first_seen_at` to the event's `ingested_at`
- sets `last_seen_at` to the event's `ingested_at`

An initial state may be created even when `source_updated_at` is absent, because
there is no existing state requiring an ordering comparison.

### `UPDATED`

Returned when both the candidate and current events have source timestamps and
the candidate timestamp is later.

The repository:

- preserves `first_seen_at`
- updates the latest event reference
- copies status, source timestamp and payload from the candidate event
- advances `last_seen_at`
- retains every historical event

A valid newer inactive event is accepted as current state. It does not delete
the advertisement or its history.

### `UNCHANGED`

Returned when the candidate event is already the event referenced by the
current-state row.

No current-state columns are modified.

### `STALE_EVENT_IGNORED`

Returned when both timestamps exist and the candidate source timestamp is
earlier than the current source timestamp.

The candidate remains stored in immutable history, but it does not replace the
current state.

### `ORDERING_UNRESOLVED`

Returned when different candidate and current events cannot be ordered
confidently.

This includes:

- equal `source_updated_at` values
- a missing candidate source timestamp
- a missing current source timestamp

The current-state row remains unchanged.

## Ordering policy

`source_updated_at` is currently the only verified source-level ordering value.

The repository does not use the following values as chronological
tie-breakers:

- PostgreSQL `event_id`
- platform `ingested_at`
- lexical or numeric source-event identifiers
- feed page order
- event type
- HTTP response order

Those values describe identity, transport or platform storage order rather than
verified NAV source chronology.

Until the live source contract provides a reliable secondary ordering value,
equal and missing source timestamps receive the conservative
`ORDERING_UNRESOLVED` outcome.

## Current-state values

The current-state row is derived from the referenced source event:

| Current-state column | Source |
|---|---|
| `source_job_id` | Typed repository input and candidate ownership |
| `latest_event_id` | Candidate event identifier |
| `source_status` | Candidate event |
| `source_updated_at` | Candidate event |
| `current_payload` | Candidate event |
| `first_seen_at` | Initial candidate `ingested_at` |
| `last_seen_at` | Accepted candidate `ingested_at` |

For updates, `last_seen_at` uses the greater of the existing value and the
candidate ingestion time. This preserves the schema requirement that
`last_seen_at` cannot move before `first_seen_at`.

## Status policy

`nav_feed_events.source_status` is nullable because the complete live source
contract has not yet been verified.

`job_advertisements_current.source_status` is mandatory.

A stored candidate event without a nonblank string status cannot create or
update current state. The repository raises a safe
`CurrentAdvertisementPersistenceError`.

## Ownership protection

The candidate lookup requires both:

- `candidate_event_id`
- `source_job_id`

The database also enforces the composite foreign key:

`(latest_event_id, source_job_id)`

referencing:

`nav_feed_events(event_id, source_job_id)`

An event belonging to another advertisement cannot become the current state.

## Concurrency protection

The repository first attempts an insert using:

`ON CONFLICT (source_job_id) DO NOTHING`

When a current row already exists, it loads and locks that row using
`SELECT ... FOR UPDATE`.

The ordering decision and any update therefore occur while the advertisement's
current-state row is locked.

This prevents an unprotected read-decide-write race between concurrent updates
for the same advertisement.

The implementation does not introduce distributed locking, advisory locks or a
custom transaction-isolation level.

## Transaction ownership

The caller owns:

- transaction creation
- commit
- rollback
- connection closure

The repository performs no commit or rollback.

This permits source-event insertion and current-state maintenance to execute in
one transaction. A caller rollback removes both writes together.

Feed-progress persistence remains outside this repository.

## Privacy and error handling

The current payload is copied from the already privacy-minimised source event.

Database constraints continue to require:

- an object-shaped JSONB payload
- no top-level `contactList`
- valid source-event ownership
- nonblank current status
- valid first-seen and last-seen ordering

Database failures are translated to
`CurrentAdvertisementPersistenceError`.

Public error messages do not include:

- database passwords
- complete connection URLs
- complete advertisement payloads
- NAV credentials
- personal contact information

The original Psycopg exception remains available through `__cause__`.

## Testing

### Python tests

The focused unit tests verify:

- all structured result outcomes
- the `changed` property
- initial-state insertion SQL
- event-derived status and payload parameters
- unchanged-event behavior
- stale-event behavior
- equal and missing timestamp behavior
- newer-event update behavior
- missing and mismatched events
- unusable status handling
- safe error translation
- absence of feed-progress SQL

### PostgreSQL integration tests

The integration tests verify:

- first-state creation
- newer-event updates
- preservation of `first_seen_at`
- advancement of `last_seen_at`
- immutable historical-event retention
- stale-event rejection
- equal-timestamp conservative behavior
- missing-timestamp conservative behavior
- inactive-state updates
- unchanged-event replay
- event ownership protection
- missing-event behavior
- unusable-status behavior
- caller rollback across both repositories
- continued connection usability
- zero feed-progress writes

All fixtures and payloads are synthetic.

## Current limitations

This milestone does not implement:

- live NAV item-to-model mapping
- a verified secondary event-ordering value
- automatic resolution of equal timestamps
- automatic resolution of missing timestamps
- feed-progress persistence
- page orchestration
- retries across pages
- connection pooling
- Prefect flows
- database roles or triggers that physically prevent source-event updates
