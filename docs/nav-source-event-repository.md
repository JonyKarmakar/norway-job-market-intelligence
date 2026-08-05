# NAV Source-Event Repository Boundary

## Purpose

This document describes the PostgreSQL persistence boundary for inserting one
validated, privacy-minimised NAV source event into `nav_feed_events`.

The repository completes the source-event insertion step without combining
HTTP retrieval, privacy processing, current-state maintenance, feed-progress
updates or orchestration.

## Implemented pipeline position

The implemented sequence is:

~~~text
Fetch one NAV feed page
    |
    v
Validate the response structure
    |
    v
Privacy-minimise the source payload
    |
    v
Validate the minimised payload
    |
    v
Calculate the deterministic SHA-256 hash
    |
    v
Insert the immutable source event
~~~

The following steps remain future work:

~~~text
Update job_advertisements_current
    |
    v
Advance nav_feed_progress
~~~

## Module responsibilities

### Database configuration

`src/norway_job_market_intelligence/config.py`

`DatabaseSettings` loads `DATABASE_URL` from the environment.

The database URL:

- is not required until persistence is attempted
- is trimmed before use
- is excluded from the settings representation
- may be injected directly during testing
- is never opened or validated at module-import time

A missing URL raises `DatabaseConfigurationError` without exposing connection
credentials.

### Connection boundary

`src/norway_job_market_intelligence/database/connection.py`

`open_database_connection()` creates one Psycopg connection when explicitly
called.

The caller owns:

- the returned connection
- transaction boundaries
- commit and rollback decisions
- connection closure

This design allows a later ingestion workflow to compose source-event
insertion, current-state maintenance and feed-progress advancement inside one
transaction.

The current implementation does not introduce connection pooling.

### Repository boundary

`src/norway_job_market_intelligence/database/repositories/nav_source_events.py`

`insert_source_event()` accepts:

- an existing Psycopg connection
- one typed `NavSourceEventInput`

The repository is responsible only for persistence into `nav_feed_events`.

It does not:

- make HTTP requests
- remove `contactList`
- calculate payload hashes
- commit or roll back transactions
- update `job_advertisements_current`
- update `nav_feed_progress`
- implement polling or pagination
- log complete source payloads
- log database credentials

## Source-event input contract

`NavSourceEventInput` contains the values required by the current migration:

| Field | Requirement |
|---|---|
| `source_event_id` | Required, nonblank and unique |
| `source_job_id` | Required and nonblank |
| `payload_hash` | Required and nonblank |
| `payload` | Required JSON object without top-level `contactList` |
| `feed_page_id` | Optional |
| `source_status` | Optional and currently unrestricted |
| `source_updated_at` | Optional timezone-aware timestamp |
| `contact_data_removed` | Must remain `True` |

PostgreSQL generates:

- `event_id`
- `ingested_at`

The repository uses Psycopg's `Jsonb` adapter rather than manually constructing
SQL JSON text.

## Parameterised insertion

All source values are passed as SQL parameters.

The repository never interpolates identifiers, statuses, timestamps, hashes or
payload values into SQL strings.

The insertion uses:

~~~sql
INSERT INTO nav_feed_events (...)
VALUES (...)
ON CONFLICT (source_event_id) DO NOTHING
RETURNING event_id
~~~

## Duplicate-event behaviour

`source_event_id` is the current duplicate-protection key.

A new event returns:

- `inserted = True`
- the generated internal `event_id`

A repeated source event returns:

- `inserted = False`
- `duplicate = True`
- the existing internal `event_id`

Duplicate handling does not update the original row.

The repository performs a lookup only after the conflict-aware insert returns
no new row. Foreign-key, check-constraint, connection and other database
failures are not classified as duplicates.

## Event immutability

The repository contains no event-update operation.

A changed advertisement with a new source-event identifier creates another
historical row. Repeating an existing source-event identifier does not replace
its job identifier, page identifier, status, timestamp, hash or payload.

Application-level immutability is supported by:

- insert-only repository SQL
- duplicate handling through `ON CONFLICT DO NOTHING`
- schema constraints
- PostgreSQL integration tests

## Transaction ownership

The repository does not call `commit()` or `rollback()`.

The caller must use an explicit transaction boundary, for example:

~~~python
with connection.transaction():
    result = insert_source_event(connection, source_event)
~~~

This permits later atomic composition:

~~~text
Insert source event
→ update current advertisement state
→ advance feed progress
→ commit once
~~~

If any composed operation fails, the caller can roll back the entire unit of
work.

## Safe error behaviour

Database failures are translated into project-level exceptions:

- `DatabaseConfigurationError`
- `DatabaseConnectionError`
- `SourceEventPersistenceError`

Public exception messages do not include:

- passwords
- complete connection URLs
- NAV tokens
- complete source payloads
- contact data

The original Psycopg exception is preserved as the internal exception cause so
tests and internal diagnostics can distinguish constraint and infrastructure
failures safely.

## Testing strategy

### Non-PostgreSQL tests

The default quality workflow excludes tests marked `postgres`.

It verifies:

- database configuration loading
- secret-safe representations
- safe connection error translation
- repository input mapping
- JSONB adaptation
- structured duplicate results
- safe persistence errors
- absence of current-state and feed-progress SQL

The complete non-PostgreSQL suite currently passes with 85 tests,
including 18 focused current advertisement-state repository tests.

### Isolated PostgreSQL tests

Run:

~~~bash
make db-repository-test
~~~

The target:

1. Waits for the Docker PostgreSQL service.
2. Reads the active container user, password and published port without
   printing the password.
3. Creates `norway_jobs_repository_test`.
4. Applies the current ingestion migration.
5. Runs only tests marked `postgres`.
6. Removes the temporary database after success or failure.

The shared PostgreSQL repository suite currently passes with 22 tests.

Ten tests remain focused on immutable source-event persistence. The additional
tests verify current advertisement-state lifecycle, ordering and transaction
behaviour.

The source-event integration tests verify:

- successful JSONB insertion
- generated internal event identifiers
- timestamp and hash preservation
- privacy-minimised payload storage
- deliberate duplicate handling
- original-row immutability
- multiple historical events for one advertisement
- visible database constraint failures
- transaction rollback after a controlled failure
- continued connection usability after rollback
- zero implicit writes from the source-event repository to
  `job_advertisements_current`
- zero writes to `nav_feed_progress`

Current-state repository behaviour is documented separately in
`docs/current-advertisement-repository.md`.

All test data is fictional.

## Current limitations

This milestone does not implement:

- complete live NAV ingestion
- automatic extraction of source identifiers from feed items
- feed-progress updates
- pagination loops
- retry orchestration
- connection pooling
- Prefect flows
- database roles that physically prohibit event updates

Current advertisement-state maintenance is now implemented as a separate
repository boundary. The two repositories remain persistence components rather
than a complete ingestion pipeline.
