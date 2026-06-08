# La Brújula del Trader - Backend Development Commands
# Usage: make [command]

.PHONY: help install dev test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (first time)
	docker compose -f docker-compose.dev.yml run --rm api poetry install

dev: ## Start development environment
	docker compose -f docker-compose.dev.yml up -d api db redis

test: ## Run tests
	docker compose -f docker-compose.dev.yml run --rm test

test-cov: ## Run tests with coverage
	docker compose -f docker-compose.dev.yml run --rm test pytest tests/ -v --cov=app --cov-report=html

logs: ## View API logs
	docker compose -f docker-compose.dev.yml logs -f api

logs-test: ## View test logs
	docker compose -f docker-compose.dev.yml logs -f test

down: ## Stop all services
	docker compose -f docker-compose.dev.yml down

clean: ## Stop and remove volumes
	docker compose -f docker-compose.dev.yml down -v

shell: ## Open shell in API container
	docker compose -f docker-compose.dev.yml exec api bash

db-shell: ## Open psql in database
	docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

migrate: ## Run Alembic migrations
	docker compose -f docker-compose.dev.yml run --rm api alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="add users table")
	docker compose -f docker-compose.dev.yml run --rm api alembic revision --autogenerate -m "$(MSG)"
