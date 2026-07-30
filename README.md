# Norway Job Market Intelligence Platform

An end-to-end data and AI platform for analysing Norwegian technology-job demand using reliable pipelines, tested analytical models, Power BI, and grounded AI.

## Project purpose

This portfolio project is designed to demonstrate practical skills relevant to:

- Junior Data Engineer
- Analytics Engineer
- Data Platform Developer
- Data Integration Developer
- Data and AI Developer
- Applied AI Developer
- BI Developer
- Research Data Engineer

The platform will ingest Norwegian job advertisements from the NAV vacancy feed, retain raw source events, transform and test analytical data, expose selected data through an API, visualise market trends, and later support narrow evidence-grounded question answering.

## Planned architecture

```text
NAV Vacancy Feed
      |
      v
Python Ingestion
      |
      v
Raw PostgreSQL
      |
      v
dbt Models and Tests
      |
      +------------------+
      |                  |
      v                  v
FastAPI              Power BI
      |
      v
Grounded AI Assistant
```

Prefect will orchestrate the pipeline. Docker Compose will support reproducible local development. GitHub Actions will run automated quality checks.

## Technology stack

- Python
- SQL
- PostgreSQL
- dbt
- Prefect
- FastAPI
- Power BI
- Docker Compose
- GitHub Actions
- One LLM provider
- One Microsoft ecosystem extension after the local MVP

## Scope boundaries

The first version intentionally excludes:

- a large frontend
- automatic job applications
- CV rewriting
- multi-agent orchestration
- scraping multiple websites
- Kafka
- Kubernetes
- multiple cloud platforms
- multiple LLM providers

## Repository structure

```text
.
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── checkpoints/
│   ├── data-source-notes.md
│   ├── decisions.md
│   ├── project-brief.md
│   ├── project-specification.md
│   └── roadmap.md
├── sql/
│   └── development/
│       └── sample_job_ads_analysis.sql
├── src/
│   └── norway_job_market_intelligence/
├── tests/
├── .editorconfig
├── .env.example
├── .gitignore
├── compose.yaml
├── Makefile
├── pyproject.toml
└── README.md
```

## Current status

**NAV feed client and privacy foundation**

The project now includes a typed and tested NAV feed client foundation, environment-backed configuration, conditional-request support, privacy minimisation, canonical JSON serialization and deterministic SHA-256 hashing.

All HTTP tests use mocked transports and do not contact the live NAV service. Live NAV ingestion, PostgreSQL persistence, pagination orchestration and feed-progress updates have not started yet.

## Local setup

### 1. Create and activate a virtual environment

macOS or Linux:

```bash
python3.11 -m venv njmi-env
source njmi-env/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv njmi-env
njmi-env\Scripts\Activate.ps1
```

### 2. Install the locked development environment

```bash
make install
```

### 3. Copy local environment variables

```bash
cp .env.example .env
```

Do not commit `.env`.

### 4. Run local checks

```bash
make quality
```

### 5. Start PostgreSQL

```bash
make db-up
```

### 6. Run the baseline SQL analysis

```bash
make sql-analysis
```
This command initializes a temporary synthetic job-advertisement dataset, runs 21 analytical queries, and rolls back the transaction so no practice data remains in PostgreSQL.

### 7. Stop PostgreSQL

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local database volume.

## Development workflow

1. Start from an updated `main`.
2. Create one focused feature branch.
3. Make a small, reviewable change.
4. Run local checks.
5. Commit with a clear conventional commit message.
6. Push the branch and open a pull request.
7. Wait for CI to pass.
8. Merge the pull request.
9. Record a checkpoint in `docs/checkpoints/`.

Example:

```bash
git switch main
git pull --ff-only
git switch -c feature/nav-feed-client-foundation

git add .
git commit -m "feat: add NAV feed client foundation"
git push -u origin feature/nav-feed-client-foundation
```

## Quality principles

- Raw source data must remain recoverable.
- Repeated pipeline execution should be idempotent.
- Source facts and AI interpretation must be distinguishable.
- Secrets must stay outside the repository.
- Data-quality assumptions must be documented and tested.
- Every milestone should produce visible portfolio evidence.
- Every pull request should remain focused and reviewable.

## Project documentation

- [Project brief](docs/project-brief.md)
- [Detailed project specification](docs/project-specification.md)
- [NAV data-source notes](docs/data-source-notes.md)
- [NAV feed client foundation](docs/nav-feed-client.md)
- [Initial NAV ingestion data model](docs/data-model-v0.md)
- [Architecture decisions](docs/decisions.md)
- [Development roadmap](docs/roadmap.md)
- [Checkpoint template](docs/checkpoints/TEMPLATE.md)
- [Week 1 Day 1 checkpoint](docs/checkpoints/0001-week1-day1-foundation.md)
