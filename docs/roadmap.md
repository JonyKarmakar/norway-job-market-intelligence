# Development Roadmap

## Week 1 — Foundation and source understanding

### Day 1

- Create the repository.
- Add the Python package structure.
- Create and activate the virtual environment.
- Add development tooling.
- Add a minimal PostgreSQL Docker service.
- Complete the SQL baseline exercise.
- Create the first checkpoint.

### Day 2

- Research and document the NAV vacancy feed contract.
- Record authentication, rate limits, pagination, identifiers, timestamps, and source-field limitations.
- Save a redacted example response outside production code.
- Define the first source-data contract.

### Day 3

- Create the initial PostgreSQL schemas.
- Add `raw`, `core`, and `meta` namespaces.
- Create the first raw-event and pipeline-run tables.
- Add migration or schema-initialisation strategy.

### Day 4

- Implement the smallest authenticated NAV API client.
- Add typed response handling, timeouts, and safe error reporting.
- Store one raw response without transforming it.

### Day 5

- Add repeatable raw ingestion.
- Add payload hashing and duplicate-event protection.
- Add tests for successful, empty, invalid, and repeated responses.
- Publish the first ingestion milestone checkpoint.

## Later phases

1. Incremental ingestion and update handling
2. dbt staging, intermediate, and mart models
3. Prefect orchestration, retries, logging, and status
4. Focused FastAPI endpoints
5. Power BI semantic model and dashboard
6. Structured skill extraction
7. Grounded assistant, evaluation, and guardrails
8. Microsoft Fabric or Copilot Studio extension
9. Portfolio packaging and demonstration
