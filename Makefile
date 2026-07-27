.PHONY: install lint format format-check test quality db-up db-down db-reset sql-analysis

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
