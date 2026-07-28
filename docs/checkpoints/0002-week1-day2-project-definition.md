# Checkpoint 0002 — Week 1 Day 2 Project Definition

## Date

2026-07-28

## Current branch

`docs/day-02-project-definition`

## Current goal

Define the project scope and document the NAV vacancy-feed contract before production ingestion begins.

## Outcome

The project now has a concise project brief, a preserved detailed specification, documented NAV source behaviour, explicit privacy and market-coverage boundaries, and accepted architecture decisions.

The selected source is the NAV `pam-stilling-feed`. The deprecated `pam-public-feed` is explicitly excluded.

The documentation distinguishes immutable privacy-minimised source events from the latest advertisement state, explains active and inactive advertisement handling, and defines the local MVP, non-goals and measurable success areas.

## Files changed

- `.env.example`
- `README.md`
- `docs/project-brief.md`
- `docs/project-specification.md`
- `docs/data-source-notes.md`
- `docs/decisions.md`
- `docs/checkpoints/0002-week1-day2-project-definition.md`

## Commands run

```bash
git switch main
git pull --ff-only origin main
git switch -c docs/day-02-project-definition
cp docs/project-brief.md docs/project-specification.md
make quality
mypy src tests
git diff --check
git status --short
```

## Tests and checks

| Check | Result | Notes |
|---|---|---|
| Ruff lint | Passed | All checks passed |
| Ruff format | Passed | 17 files already formatted |
| Pytest | Passed | 2 tests passed |
| Mypy | Passed | No issues found in 8 source files |
| dbt tests | Not run | dbt has not been introduced |
| Docker smoke test | Not run | No runtime or database changes were made |
| Manual verification | Passed | Documentation, links, stale references and token naming reviewed |
| Secret review | Passed | No NAV token or personal contact data added |

## Commit status

- Commit: Created locally as `docs: define project scope and NAV feed strategy`
- Push: Not pushed
- Pull request: Not opened
- CI: Not started
- Merge: Not applicable yet

## Decisions made

- Use NAV `pam-stilling-feed` as the only vacancy source for the local MVP.
- Do not use the deprecated `pam-public-feed`.
- Store privacy-minimised source events separately from current advertisement state.
- Remove the source `contactList` before persistent storage.
- Exclude personal contact information from analytics, APIs, logs, fixtures and AI retrieval.
- Build the complete local MVP before adding a Microsoft ecosystem extension.
- Publish explicit limitations stating that NAV feed data is not the complete Norwegian job market.
- Preserve the detailed planning document as `docs/project-specification.md`.
- Keep `docs/project-brief.md` concise and user-focused.
- Standardise the NAV credential variable as `NAV_FEED_TOKEN`.

## Known limitations

- No production NAV client has been implemented.
- No live or redacted feed response has been committed.
- Exact endpoint schemas and error responses require implementation-time verification.
- A numerical rate limit or recommended polling interval has not been confirmed.
- Timestamp relationships and enum values require validation against real responses.
- Initial PostgreSQL schemas will be designed during Day 3.
- GitHub CI has not yet run for the Day 2 branch.

## Next exact task

Push the Day 2 branch and open the pull request.

## Next command

```bash
git push -u origin docs/day-02-project-definition
```
