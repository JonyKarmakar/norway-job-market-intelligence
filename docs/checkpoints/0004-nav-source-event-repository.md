# Checkpoint 0004 — NAV source-event repository boundary

## Date

2026-08-02

## Current branch

`docs/nav-source-event-repository-checkpoint`

## Current goal

Record the completed PostgreSQL repository milestone for inserting one
validated, privacy-minimised NAV source event.

## Outcome

The project now has a tested PostgreSQL persistence boundary for inserting
immutable NAV source events into `nav_feed_events`.

The implementation adds safe database configuration, caller-owned Psycopg
connections, typed source-event inputs, parameterised JSONB insertion,
deliberate duplicate handling and isolated PostgreSQL integration tests.

The repository does not update current advertisement state or feed progress.

## Files changed

### Application code

- `src/norway_job_market_intelligence/config.py`
- `src/norway_job_market_intelligence/database/connection.py`
- `src/norway_job_market_intelligence/database/exceptions.py`
- `src/norway_job_market_intelligence/database/repositories/__init__.py`
- `src/norway_job_market_intelligence/database/repositories/nav_source_events.py`

### Tests

- `tests/test_database_config.py`
- `tests/test_database_connection.py`
- `tests/test_nav_source_event_repository.py`
- `tests/integration/test_nav_source_event_repository_postgres.py`

### Tooling and CI

- `Makefile`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `.github/workflows/ci.yml`

### Documentation

- `README.md`
- `docs/data-model-v0.md`
- `docs/decisions.md`
- `docs/nav-feed-client.md`
- `docs/nav-source-event-repository.md`

## Commands run

    make install
    make quality
    make sql-analysis
    make db-schema-test
    make db-repository-test
    make dependency-check
    git diff --check

## Tests and checks

| Check | Result | Notes |
|---|---|---|
| Ruff lint | Passed | Complete project |
| Ruff format | Passed | Complete project |
| Strict MyPy | Passed | 22 source files |
| Non-PostgreSQL Pytest | Passed | 67 tests |
| PostgreSQL integration tests | Passed | 10 tests |
| Total tests | Passed | 77 tests |
| Analytical SQL | Passed | 21 analyses |
| Schema verification | Passed | Positive lifecycle and negative constraints |
| Dependency integrity | Passed | No broken requirements |
| Docker PostgreSQL | Passed | PostgreSQL 16 Alpine |
| Live NAV request | Not run | All NAV HTTP tests remained mocked |
| Git diff validation | Passed | No whitespace errors |

## Commit status

- Feature commits:
  - `3b6d1d4` — `feat: add NAV source-event repository`
  - `062a80a` — `docs: document NAV source-event repository`
- Pull request: #8
- Pull-request CI: Passed
- Squash merge commit: `a26f0d6533370ac5ba3fb82c249156be738b0c9d`
- Post-merge CI run: `30744397821`
- Post-merge CI: Passed

## Decisions made

- Use Psycopg 3 with the binary installation extra.
- Load `DATABASE_URL` only when database persistence is requested.
- Exclude the complete database URL from representations and public errors.
- Pass an existing connection into the repository.
- Keep commit, rollback and connection closure under caller ownership.
- Use parameterised SQL and Psycopg JSONB adaptation.
- Use `source_event_id` as the current duplicate-protection key.
- Return a structured duplicate result with the existing internal event ID.
- Preserve source-event immutability through insert-only repository behaviour.
- Keep current-state and feed-progress writes outside this repository.
- Test persistence against an isolated temporary PostgreSQL database.
- Record the design in ADR-009.

## Known limitations

- Live NAV ingestion is not implemented.
- Source-event values are not automatically extracted from feed items.
- `job_advertisements_current` is not updated.
- `nav_feed_progress` is not updated.
- Pagination, retries and Prefect orchestration are not implemented.
- Connection pooling is not included.
- Database roles or triggers do not physically prohibit event updates.

## Next exact task

Implement the PostgreSQL repository boundary for maintaining
`job_advertisements_current` from an accepted source event while preserving
`first_seen_at`.

Do not update `nav_feed_progress` in that milestone.

## Next command

    git switch main
