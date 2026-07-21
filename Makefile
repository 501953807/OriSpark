.PHONY: help install db-init db-migrate db-revision backend frontend electron portal miniprogram celery test lint format clean docker-build docker-up docker-down all deps

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend-web dependencies..."
	cd frontend-web && npm install
	@echo "Dependencies installed!"

db-init: ## Initialize database and seed data
	cd backend && python3 -m app.database --init

db-migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

db-revision: ## Create new Alembic migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

backend: ## Start backend API only
	@bash scripts/start-backend.sh

frontend: ## Start frontend Web only
	@bash scripts/start-frontend.sh

electron: ## Start Electron desktop app
	@bash scripts/start-electron.sh

portal: ## Start Nuxt portal
	@bash scripts/start-portal.sh

miniprogram: ## Start WeChat mini-program
	@bash scripts/start-miniprogram.sh

celery: ## Start Celery worker and beat
	@bash scripts/start-celery.sh

test: ## Run all tests
	@bash scripts/check-deps.sh
	cd backend && pytest tests/ -v
	cd frontend-web && npx vitest run

test-backend: ## Run backend tests only
	cd backend && pytest tests/ -v

test-frontend: ## Run frontend tests only
	cd frontend-web && npx vitest run

lint: ## Run linters
	cd backend && ruff check app/
	cd frontend-web && npx eslint src/

format: ## Format code
	cd backend && ruff format app/
	cd frontend-web && npx prettier --write src/

clean: ## Clean build artifacts
	rm -rf backend/__pycache__ backend/app/__pycache__
	rm -rf frontend-web/dist frontend-web/.vite
	rm -rf backend/data/certificates/*
	@echo "Clean complete."

all: ## Start all available services
	@bash scripts/start-all.sh

deps: ## Check environment dependencies
	@bash scripts/check-deps.sh

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start Docker services
	docker compose up -d

docker-down: ## Stop Docker services
	docker compose down
