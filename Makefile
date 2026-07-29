.PHONY: install lint format format-check test quality db-up db-down db-reset sql-analysis db-schema-test

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

format-check:
	ruff format --check .

test:
	pytest

quality: lint format-check test

db-up:
	docker compose up -d db
	docker compose ps

db-down:
	docker compose down

db-reset:
	docker compose down -v

sql-analysis:
	docker compose exec -T db psql -U njmi -d norway_jobs < sql/development/sample_job_ads_analysis.sql

db-schema-test:
	@set -eu; \
	test_db="norway_jobs_schema_test"; \
	docker compose exec -T db dropdb -U njmi --if-exists "$$test_db"; \
	trap 'docker compose exec -T db dropdb -U njmi --if-exists "$$test_db" >/dev/null' EXIT; \
	docker compose exec -T db createdb -U njmi "$$test_db"; \
	docker compose exec -T db psql -v ON_ERROR_STOP=1 -U njmi -d "$$test_db" < sql/migrations/001_create_nav_ingestion_schema.sql; \
	docker compose exec -T db psql -v ON_ERROR_STOP=1 -U njmi -d "$$test_db" < sql/development/verify_nav_ingestion_schema.sql
