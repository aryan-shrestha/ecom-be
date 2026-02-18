.PHONY: help install dev db-up db-down db-reset migrate seed keys server test lint format clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv pip install -e ".[dev]"

dev: ## Install dev dependencies
	uv pip install -e ".[dev]"

db-up: ## Start PostgreSQL with Docker
	docker-compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3

db-down: ## Stop PostgreSQL
	docker-compose down

db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d
	@sleep 3
	alembic upgrade head

migrate: ## Run database migrations
	alembic upgrade head

seed: ## Seed database with initial data
	python scripts/seed_data.py

keys: ## Generate JWT keys
	python scripts/generate_keys.py

server: ## Run development server
	uvicorn app.presentation.api.main:app --reload

test: ## Run tests
	pytest -v

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linter
	ruff check .

format: ## Format code
	ruff format .

type-check: ## Run type checker
	mypy app/

check: lint format type-check ## Run all checks

clean: ## Clean up cache and temp files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage

setup: db-up keys migrate seed ## Complete setup (DB + keys + migrations + seed)
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Run 'make server' to start the server"
