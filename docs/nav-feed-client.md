# NAV Feed Client Foundation

## Purpose

This document describes the initial Python foundation for retrieving individual
pages from the NAV `pam-stilling-feed` and preparing advertisement payloads for
privacy-safe persistence.

The implementation deliberately separates HTTP retrieval, privacy processing
and future database operations.

## Current scope

The current foundation implements:

1. Environment-backed NAV feed configuration.
2. Bearer-authenticated retrieval of one feed page.
3. Conditional requests using `ETag` and `Last-Modified`.
4. Structured feed-page response handling.
5. Privacy minimisation of advertisement payloads.
6. Privacy-boundary validation.
7. Canonical JSON serialization.
8. Deterministic SHA-256 payload hashing.
9. Mocked unit tests without live NAV requests.
10. Reproducible dependency locking and shared local and CI quality checks.

The current foundation does not implement:

- complete pagination loops
- scheduled polling
- retry policies across feed pages
- current-state upserts
- feed-progress updates
- Prefect orchestration
- live NAV ingestion
- dbt transformations
- FastAPI endpoints
- Power BI integration

These responsibilities belong to later focused milestones.

## Module responsibilities

### Configuration

`src/norway_job_market_intelligence/config.py`

`NavFeedSettings` loads:

- `NAV_FEED_TOKEN`
- `NAV_FEED_URL`
- `NAV_FEED_TIMEOUT_SECONDS`
- `NAV_FEED_USER_AGENT`

The settings object is immutable.

The token is excluded from the dataclass representation to reduce accidental
secret exposure during debugging. Configuration may be created without a token,
but an authenticated request cannot begin until a token is available.

### Project exceptions

`src/norway_job_market_intelligence/ingestion/exceptions.py`

The project translates configuration, transport, authentication, response and
privacy failures into narrow application-level exceptions.

Exception messages do not include:

- the Bearer token
- complete source payloads
- server response bodies
- personal contact information

### HTTP client

`src/norway_job_market_intelligence/ingestion/nav_client.py`

`NavFeedClient` is a synchronous HTTPX client responsible for requesting one
feed page at a time.

The client:

- sends Bearer authentication
- sends an explicit user agent
- applies a configurable timeout
- accepts optional `If-None-Match`
- accepts optional `If-Modified-Since`
- handles `304 Not Modified` without parsing a response body
- returns response status and conditional-request metadata
- validates the page payload and its `items` array
- resolves relative `next_url` values
- rejects unsafe or unexpected URLs
- disables automatic redirects
- closes HTTP resources through a context manager or explicit `close()`

The client does not iterate through the feed or write data to PostgreSQL.

## Structured page result

A successful request returns `NavFeedPageResult` with:

- `request_url`
- `status_code`
- `payload`
- `items`
- `next_url`
- `etag`
- `last_modified`
- `not_modified`

For a `304 Not Modified` response:

- `status_code` is `304`
- `payload` is `None`
- `items` is empty
- `next_url` is `None`
- `not_modified` is `True`

## URL and authentication security

Bearer credentials must only be sent to the configured feed origin.

The client therefore validates that:

- the configured feed URL is an absolute HTTP or HTTPS URL
- URLs do not contain embedded usernames or passwords
- URLs do not contain fragments
- explicitly requested page URLs use the configured feed origin
- response-provided `next_url` values use the response origin

Automatic redirect following is disabled. An unexpected redirect is treated as
an unsuccessful request instead of forwarding credentials automatically.

## Feed-page validation

A successful page response must contain a JSON object.

The object must contain:

- `items` as an array
- every item as a JSON object

`next_url` may be:

- a non-empty string
- `null`
- absent

Invalid JSON and invalid response structures produce distinct project
exceptions.

## Privacy-processing sequence

`src/norway_job_market_intelligence/ingestion/privacy.py`

The required processing order is:

~~~text
Source payload
    |
    v
Validate source is a JSON object
    |
    v
Create a deep copy
    |
    v
Remove top-level contactList
    |
    v
Validate the minimised payload
    |
    v
Serialize canonical JSON
    |
    v
Calculate SHA-256 hash
~~~

### Minimisation boundary

Only the top-level `contactList` key is removed.

The implementation does not recursively remove nested fields because recursive
removal has not been justified by the documented source contract.

The source object is not mutated.

### Validation boundary

A persistent payload must:

- be a JSON object
- use string object keys
- contain no top-level `contactList`
- contain only JSON-serializable values
- contain no non-finite numeric values

### Canonical hashing

The payload hash is calculated after privacy minimisation using:

- JSON keys sorted lexicographically
- compact separators
- UTF-8 encoding
- Unicode retained without ASCII escaping
- non-finite numbers rejected
- SHA-256 hashing

Equivalent objects with different key insertion order produce the same hash.
Changed values produce a different hash.

`calculate_payload_hash()` rejects a payload that still contains a top-level
`contactList`, preventing accidental hashing of an unminimised source payload.

## Testing strategy

The implementation has focused tests for:

- configuration defaults and overrides
- missing and invalid configuration
- secret-safe object representations
- request and conditional headers
- successful feed-page parsing
- `304 Not Modified`
- authentication failures
- unsuccessful HTTP statuses
- redirects
- invalid JSON
- invalid response structures
- same-origin URL enforcement
- timeouts and transport failures
- token-safe exception messages
- source immutability
- top-level contact removal
- serialization validation
- deterministic hashing
- complete minimise-and-hash processing

All HTTP tests use `httpx.MockTransport`.

No unit test calls the live NAV service.

## Dependency reproducibility

`pyproject.toml` is the source of truth for direct project dependencies.

Generated lock files provide exact dependency versions and package hashes:

- `requirements.txt` for runtime dependencies
- `requirements-dev.txt` for runtime and development dependencies

Regenerate both lock files with:

~~~bash
make lock-dependencies
~~~

Install the locked development environment with:

~~~bash
make install
~~~

The lock files are generated using Python 3.11 and pip-tools.

## Quality workflow

The shared local and CI quality command is:

~~~bash
make quality
~~~

It runs:

1. Ruff linting.
2. Ruff formatting verification.
3. Strict MyPy type checking.
4. The non-PostgreSQL Pytest suite.

PostgreSQL repository tests run separately through:

~~~bash
make db-repository-test
~~~

GitHub Actions installs the hash-verified development environment and runs both
the Python quality workflow and the database-dependent schema and repository
checks.

## Future integration order

The intended end-to-end ingestion order is:

1. Fetch one feed page.
2. Validate the page response.
3. Privacy-minimise each accepted advertisement payload.
4. Validate each minimised payload.
5. Calculate its deterministic hash.
6. Insert the immutable source event.
7. Update the current advertisement state.
8. Advance feed progress only after successful processing.

The project now completes steps 1 through 6.

Source-event persistence is documented separately in
`docs/nav-source-event-repository.md`. Current-state updates and feed-progress
advancement remain future milestones.
