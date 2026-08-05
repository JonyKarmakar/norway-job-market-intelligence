# Checkpoint 0005 — Current advertisement-state repository

## Date

2026-08-05

## Current branch

`docs/current-advertisement-repository-checkpoint`

## Current goal

Record the completed PostgreSQL repository milestone for maintaining
`job_advertisements_current` from an accepted immutable NAV source event.

## Outcome

The project now has a tested PostgreSQL persistence boundary for creating and
maintaining the latest known state of each NAV advertisement.

The repository derives status, source timestamps, ingestion timestamps and the
privacy-minimised payload directly from the stored candidate event. This keeps
the current-state row consistent with immutable source-event history.

The repository returns explicit outcomes for:

- newly created current state
- successfully updated current state
- reprocessing the event that is already current
- ignoring a demonstrably older event
- refusing to choose between events when ordering is unresolved

A candidate replaces the current state only when both source timestamps exist
and the candidate timestamp is newer. Equal or missing timestamps do not use
event IDs, ingestion order or response order as chronological tie-breakers.

The implementation preserves `first_seen_at`, advances `last_seen_at` without
regression, accepts newer inactive states, locks an existing current row during
comparison and leaves commit, rollback and connection closure under caller
ownership.

The repository does not update `nav_feed_progress`.

## Files changed

### Application code

- `src/norway_job_market_intelligence/database/exceptions.py`
- `src/norway_job_market_intelligence/database/repositories/current_advertisements.py`

### Tests

- `tests/test_current_advertisement_repository.py`
- `tests/integration/test_current_advertisement_repository_postgres.py`

### Tooling and CI

- `Makefile`
- `.github/workflows/ci.yml`

### Documentation

- `README.md`
- `docs/current-advertisement-repository.md`
- `docs/data-model-v0.md`
- `docs/decisions.md`
- `docs/nav-feed-client.md`
- `docs/nav-source-event-repository.md`

## Commands run

    make quality
    make sql-analysis
    make db-schema-test
    make db-repository-test
    make dependency-check
    git diff --check
    gh pr checks 10
    gh pr merge 10 --squash --delete-branch

## Tests and checks

| Check | Result | Notes |
|---|---|---|
| Ruff lint | Passed | Complete project |
| Ruff format | Passed | Complete project |
| Strict MyPy | Passed | 25 configured source files |
| Non-PostgreSQL Pytest | Passed | 85 tests |
| PostgreSQL integration tests | Passed | 22 tests |
| Total tests | Passed | 107 tests |
| Current-state unit tests | Passed | 18 focused tests |
| Current-state PostgreSQL cases | Passed | 12 cases |
| Analytical SQL | Passed | 21 analyses |
| Schema verification | Passed | Positive lifecycle and negative constraints |
| Dependency integrity | Passed | No broken requirements |
| Docker PostgreSQL | Passed | PostgreSQL 16 Alpine |
| Transaction rollback | Passed | Source event and current state rolled back together |
| Live NAV request | Not run | All NAV HTTP tests remained mocked |
| Pull-request CI | Passed | Two required jobs |
| Post-merge CI | Passed | Run 31050628017 |
| Git diff validation | Passed | No whitespace errors |

## Commit status

- Feature commits:
  - `94929c5` — `feat: add current advertisement repository`
  - `b4f7c47` — `test: verify current advertisement lifecycle`
  - `28b8043` — `docs: document current advertisement ordering policy`
- Pull request: #10
- Pull-request CI: Passed
- Squash merge commit: `b2c142976b8780af3ff2656d0590c91506941b73`
- Post-merge CI run: `31050628017`
- Post-merge CI: Passed

## Decisions made

- Accept only a stored source-event identifier and source job identifier as
  repository input.
- Derive current-state values from the immutable candidate event instead of
  accepting duplicate caller-provided state.
- Create the first current-state row even when the source timestamp is absent.
- Update existing state only when the candidate source timestamp is
  demonstrably newer.
- Return `UNCHANGED` when the candidate event is already current.
- Return `STALE_EVENT_IGNORED` for a demonstrably older candidate.
- Return `ORDERING_UNRESOLVED` when either timestamp is missing or equal across
  different events.
- Do not use internal event IDs, ingestion timestamps, source-event IDs, page
  order or response order as chronology.
- Preserve `first_seen_at`.
- Set or advance `last_seen_at` using the accepted candidate ingestion time
  without allowing it to regress.
- Keep newer inactive advertisements as the current known state rather than
  deleting the row.
- Lock an existing current-state row with `SELECT ... FOR UPDATE` before
  comparison and mutation.
- Keep commit, rollback and connection closure under caller ownership.
- Keep feed-progress writes outside this repository.
- Translate Psycopg failures into a safe current-advertisement persistence
  exception while retaining the original exception as the cause.
- Record the conservative ordering design in ADR-010.

## Known limitations

- `nav_feed_progress` is not read or updated.
- Complete feed-page transaction orchestration is not implemented.
- Pagination loops and retry orchestration are not implemented.
- Prefect flows are not implemented.
- Live NAV ingestion is not implemented.
- Connection pooling is not included.
- Equal or missing source timestamps remain deliberately unresolved.
- No alternative validated source-ordering field is available.
- Database roles or triggers do not physically prohibit source-event updates.
- GitHub Actions emitted non-blocking Node.js 20 deprecation annotations for
  `actions/checkout@v4` and `actions/setup-python@v5`.

## Next exact task

Implement a PostgreSQL repository boundary for reading and advancing
`nav_feed_progress` only after the caller confirms that all source-event and
current-state writes for a feed page succeeded.

Do not add pagination loops, retry orchestration or Prefect flows in that
repository milestone.

## Next command

    git switch main
