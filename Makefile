.PHONY: install install-dev lock-dependencies lint format format-check type-check test quality db-up db-down db-reset sql-analysis db-schema-test

install: install-dev

install-dev:
	python -m pip install --disable-pip-version-check --require-hashes -r requirements-dev.txt
	python -m pip install --disable-pip-version-check --no-deps --no-build-isolation -e .

lock-dependencies:
	python -m piptools compile --resolver=backtracking --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file=requirements.txt pyproject.toml
	python -m piptools compile --resolver=backtracking --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url --no-emit-trusted-host --extra=dev --output-file=requirements-dev.txt pyproject.toml

lint:
	python -m ruff check .

format:
	python -m ruff format .
	python -m ruff check --fix .

format-check:
	python -m ruff format --check .

type-check:
	python -m mypy src tests

test:
	python -m pytest

quality: lint format-check type-check test

db-up:
	docker compose up -d --wait db
	docker compose ps

db-down:
	docker compose down

db-reset:
	docker compose down -v

sql-analysis: db-up
	docker compose exec -T db psql -U njmi -d norway_jobs < sql/development/sample_job_ads_analysis.sql

db-schema-test: db-up
	@set -eu; \
	test_db="norway_jobs_schema_test"; \
	docker compose exec -T db dropdb -U njmi --if-exists "$$test_db"; \
	trap 'docker compose exec -T db dropdb -U njmi --if-exists "$$test_db" >/dev/null' EXIT; \
	docker compose exec -T db createdb -U njmi "$$test_db"; \
	docker compose exec -T db psql -v ON_ERROR_STOP=1 -U njmi -d "$$test_db" < sql/migrations/001_create_nav_ingestion_schema.sql; \
	docker compose exec -T db psql -v ON_ERROR_STOP=1 -U njmi -d "$$test_db" < sql/development/verify_nav_ingestion_schema.sql
