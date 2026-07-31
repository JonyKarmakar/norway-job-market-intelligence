# Checkpoint 0003 — NAV Feed Client Foundation

## Date

2026-07-30

## Current branch

`docs/nav-feed-client-checkpoint`

## Current goal

Record the completed and merged NAV feed client, privacy-processing and dependency-reproducibility milestone.

## Outcome

The project now has a typed and tested Python foundation for retrieving one page
from the NAV `pam-stilling-feed`.

The HTTP client supports:

- environment-backed configuration
- Bearer authentication
- configurable timeout and user agent
- `ETag` and `Last-Modified` conditional requests
- structured `304 Not Modified` handling
- response and feed-item structure validation
- relative `next_url` resolution
- same-origin enforcement
- disabled automatic redirects
- safe project-level exceptions

The privacy-processing module:

- deep-copies the source payload
- removes only the top-level `contactList`
- validates the minimised JSON object
- rejects non-JSON and non-finite values
- produces canonical JSON
- calculates a deterministic SHA-256 hash after minimisation

All HTTP tests use `httpx.MockTransport`; no automated test contacts the live
NAV service.

The dependency workflow now uses hash-verified runtime and development lock
files generated with pip-tools. Local development and GitHub Actions run the
same `make quality` target.

Database commands now wait for PostgreSQL health before executing, removing the
startup race identified during local SQL validation.

The milestone implements ingestion processing steps 1 through 5 only:

1. Fetch one feed page.
2. Validate the page response.
3. Privacy-minimise accepted payloads.
4. Validate minimised payloads.
5. Calculate deterministic hashes.

## Files changed

- `.env.example`
- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `docs/data-model-v0.md`
- `docs/decisions.md`
- `docs/nav-feed-client.md`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `src/norway_job_market_intelligence/config.py`
- `src/norway_job_market_intelligence/ingestion/exceptions.py`
- `src/norway_job_market_intelligence/ingestion/nav_client.py`
- `src/norway_job_market_intelligence/ingestion/privacy.py`
- `tests/test_nav_feed_client.py`
- `tests/test_nav_feed_config.py`
- `tests/test_nav_feed_privacy.py`

## Commands run

```bash
make quality
make sql-analysis
make db-schema-test
python -m pip check
git diff --check
gh pr checks
gh pr merge 6 --squash --delete-branch
gh run watch 30571684311 --exit-status
```

Runtime and development lock files were also installed in temporary clean
Python 3.11 environments using hash verification.

## Tests and checks

| Check | Result | Notes |
|---|---|---|
| Ruff lint | Passed | All checks passed |
| Ruff format | Passed | 26 files verified |
| MyPy | Passed | No issues found in 14 source files |
| Pytest | Passed | 52 tests passed |
| Runtime lock installation | Passed | Installed from `requirements.txt` with hash verification |
| Development lock installation | Passed | Installed from `requirements-dev.txt`; editable project and quality checks passed |
| SQL analysis | Passed | All 21 analytical queries completed and the transaction rolled back |
| Database schema verification | Passed | Positive lifecycle and negative constraint checks passed |
| PostgreSQL readiness | Passed | `docker compose up -d --wait db` removed the startup race |
| Pull-request CI | Passed | `python-quality` and `database-schema` succeeded |
| Main push CI | Passed | Run `30571684311` completed successfully |
| Dependency integrity | Passed | `python -m pip check` found no broken requirements |
| Whitespace review | Passed | `git diff --check` returned no errors |
| Secret review | Passed | No real NAV credential or personal contact data was committed |
| Live NAV request | Not run | Intentionally excluded from automated testing |

## Commit status

- Commit: Feature commit `6e6f3b4` created as `feat: add NAV feed client foundation`
- Push: Pushed to `origin/feature/nav-feed-client-foundation`
- Pull request: PR #6, `Add NAV feed client and privacy foundation`
- CI: Pull-request checks and post-merge `main` checks passed
- Merge: Squash-merged into `main` as `825bdf7`
- Cleanup: Local and remote feature branches deleted
- Repository state: Local `main` synchronized with `origin/main`

## Decisions made

- Keep the NAV HTTP client responsible for one feed page only.
- Keep pagination, persistence and orchestration outside the HTTP client.
- Send Bearer credentials only to the configured feed origin.
- Disable automatic redirect following.
- Remove the top-level `contactList` before hashing or future persistence.
- Do not mutate the original source payload during privacy minimisation.
- Validate the minimised payload before canonical serialization.
- Use deterministic SHA-256 hashing over canonical UTF-8 JSON.
- Do not use the payload hash as the initial event uniqueness key.
- Use `pyproject.toml` for direct dependency constraints.
- Commit hash-verified runtime and development lock files.
- Use `python -m` commands through the Makefile to avoid environment ambiguity.
- Run the same quality target locally and in GitHub Actions.
- Make database-dependent targets wait for PostgreSQL readiness.
- Keep all automated HTTP tests isolated from the live NAV service.

These client and privacy decisions are recorded as ADR-007 and ADR-008.

## Known limitations

- No live NAV request has been performed by the implementation tests.
- No complete pagination loop exists.
- No PostgreSQL source-event insertion exists.
- No current-advertisement upsert exists.
- No feed-progress update exists.
- No multi-page retry policy exists.
- No scheduled polling or Prefect orchestration exists.
- No live NAV payload has been committed.
- Runtime endpoint details still require cautious verification during live integration.
- The final retention period for privacy-minimised events remains undefined.

## Next exact task

Implement the PostgreSQL repository boundary for inserting one validated,
privacy-minimised NAV source event without yet updating current advertisement
state or feed progress.

## Next command

```bash
git add docs/checkpoints/0003-nav-feed-client-foundation.md
```
