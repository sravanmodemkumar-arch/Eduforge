# =============================================================================
# EduForge Makefile
# Common development tasks for the EduForge platform
# =============================================================================

.DEFAULT_GOAL := help

COMPOSE := docker compose
SERVICES := identity portal exam notification billing ai analytics

# -----------------------------------------------------------------------------
# Docker Compose
# -----------------------------------------------------------------------------

.PHONY: up
up: ## Start all services in detached mode
	$(COMPOSE) up -d

.PHONY: down
down: ## Stop and remove all containers
	$(COMPOSE) down

.PHONY: build
build: ## Build (or rebuild) all service images
	$(COMPOSE) build

.PHONY: logs
logs: ## Tail logs for all services (use: make logs service=identity)
ifdef service
	$(COMPOSE) logs -f $(service)
else
	$(COMPOSE) logs -f
endif

.PHONY: restart
restart: ## Restart all services (or a specific one: make restart service=identity)
ifdef service
	$(COMPOSE) restart $(service)
else
	$(COMPOSE) restart
endif

.PHONY: ps
ps: ## Show running containers
	$(COMPOSE) ps

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

.PHONY: test
test: ## Run tests across all services
	@for svc in $(SERVICES); do \
		echo "\n========== Testing $$svc =========="; \
		$(COMPOSE) exec -T $$svc pytest tests/ -v || true; \
	done

.PHONY: test-service
test-service: ## Run tests for a specific service (use: make test-service service=identity)
	$(COMPOSE) exec -T $(service) pytest tests/ -v

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff linter on all services
	ruff check services/ packages/

.PHONY: format
format: ## Auto-format code with ruff
	ruff format services/ packages/
	ruff check --fix services/ packages/

.PHONY: typecheck
typecheck: ## Run mypy type checking
	mypy services/ packages/

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

.PHONY: migrate
migrate: ## Run database migrations for all services
	@for svc in $(SERVICES); do \
		echo "\n========== Migrating $$svc =========="; \
		if [ "$$svc" = "portal" ]; then \
			$(COMPOSE) exec -T $$svc python manage.py migrate || true; \
		else \
			$(COMPOSE) exec -T $$svc alembic upgrade head || true; \
		fi; \
	done

.PHONY: db-reset
db-reset: ## Reset the database (WARNING: destroys all data)
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5
	$(COMPOSE) up -d

# -----------------------------------------------------------------------------
# Shell Access
# -----------------------------------------------------------------------------

.PHONY: shell-identity
shell-identity: ## Open a shell in the identity service container
	$(COMPOSE) exec identity /bin/bash

.PHONY: shell-portal
shell-portal: ## Open a shell in the portal service container
	$(COMPOSE) exec portal /bin/bash

.PHONY: shell-exam
shell-exam: ## Open a shell in the exam service container
	$(COMPOSE) exec exam /bin/bash

.PHONY: shell-notification
shell-notification: ## Open a shell in the notification service container
	$(COMPOSE) exec notification /bin/bash

.PHONY: shell-billing
shell-billing: ## Open a shell in the billing service container
	$(COMPOSE) exec billing /bin/bash

.PHONY: shell-ai
shell-ai: ## Open a shell in the AI service container
	$(COMPOSE) exec ai /bin/bash

.PHONY: shell-analytics
shell-analytics: ## Open a shell in the analytics service container
	$(COMPOSE) exec analytics /bin/bash

.PHONY: shell-db
shell-db: ## Open a psql shell to the database
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-eduforge} -d $${POSTGRES_DB:-eduforge}

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@echo "EduForge Development Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
