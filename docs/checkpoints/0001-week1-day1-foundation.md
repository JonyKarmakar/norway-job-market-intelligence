# Checkpoint 0001 — Week 1 Day 1 Foundation

## Date

2026-07-27

## Current branch

`main`

## Current goal

Create a professional repository foundation with Python tooling, PostgreSQL local development, automated quality checks, CI configuration, documentation, and a baseline SQL analysis.

## Outcome

The initial project scaffold has been configured and verified locally.

The repository now includes:

- A Python 3.11 package structure
- A project-specific virtual environment
- Ruff, Pytest, and MyPy development tooling
- A PostgreSQL 16 Docker service
- A professional Makefile workflow
- A GitHub Actions CI workflow
- Project documentation and checkpoint templates
- Smoke tests
- A reproducible SQL analysis using synthetic job-advertisement data
- Eight completed baseline SQL analyses
- Transaction rollback to prevent temporary analysis data from persisting

The local Git repository has been initialized on the `main` branch, and the verified project foundation has been recorded in the root commit. The repository has not yet been pushed to GitHub.

## Files changed

- `README.md`
- `pyproject.toml`
- `.gitignore`
- `.env.example`
- `.editorconfig`
- `compose.yaml`
- `Makefile`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `src/norway_job_market_intelligence/`
- `tests/test_project_smoke.py`
- `sql/development/sample_job_ads_analysis.sql`
- `docs/project-brief.md`
- `docs/roadmap.md`
- `docs/checkpoints/TEMPLATE.md`
- `docs/checkpoints/0001-week1-day1-foundation.md`

The local `.env` file contains development credentials and remains excluded from Git.

## Commands run

```bash
python3.11 -m venv njmi-env
source njmi-env/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

ruff check .
ruff format --check .
pytest
mypy src tests

docker compose config --services
docker compose up -d db
docker compose ps
docker compose exec -T db psql -U njmi -d norway_jobs
make sql-analysis

git init -b main
git status --short
```

## Tests and checks

| Check | Result | Notes |
|---|---|---|
| Ruff lint | Passed | `All checks passed!` |
| Ruff format | Passed | 14 files were already formatted |
| Pytest | Passed | 2 tests passed |
| MyPy | Passed | No issues found in 8 source files |
| PostgreSQL health | Passed | Container reached healthy status |
| PostgreSQL connection | Passed | Connected to `norway_jobs` as user `njmi` |
| SQL baseline analysis | Passed | Eight analyses completed successfully |
| SQL transaction cleanup | Passed | Analysis ended with `ROLLBACK` |
| Git repository initialization | Passed | Repository initialized on `main` |
| GitHub Actions | Not run | Requires the first GitHub push or pull request |

## Commit status

- Commit: Created as the repository root commit
- Commit message: `chore: establish project foundation`
- Push: Not pushed
- Pull request: Not opened
- CI: Not started
- Merge: Not applicable

## Decisions made

- Python 3.11 is the initial development baseline.
- The local virtual environment is named `njmi-env`.
- PostgreSQL 16 is used for local development.
- Docker Compose manages the local database service.
- Local credentials are stored in `.env`, which is excluded from Git.
- The initial CI workflow covers Ruff linting, formatting validation, and Python tests.
- MyPy is currently executed locally and may be added to CI in a later improvement.
- Project-related SQL belongs in the repository when it supports development, validation, transformation, or analysis.
- Tutorial-style SQL practice folders were removed before the first commit.
- The completed baseline analysis is stored in `sql/development/`.
- Synthetic analysis data is created inside a transaction and removed using `ROLLBACK`.
- NAV ingestion, dbt, Prefect, FastAPI, Power BI, and AI implementation are deferred to focused later milestones.
- One Microsoft ecosystem extension will be implemented after the local MVP is stable.
- Every pull request or milestone will receive a numbered checkpoint document.

## Known limitations

- The repository is not yet connected to the NAV vacancy feed.
- No persistent application database schema exists yet.
- No raw job-advertisement ingestion pipeline exists yet.
- No incremental loading or duplicate-handling logic exists yet.
- No dbt project or Prefect flow exists yet.
- No FastAPI application endpoint exists yet.
- No Power BI model or dashboard exists yet.
- The current SQL analysis uses temporary synthetic data.
- CI has not yet been executed on GitHub.

## Next exact task

Connect the local repository to a GitHub repository, push the `main` branch, and verify the first GitHub Actions CI run.

## Next command

```bash
git remote -v
```
