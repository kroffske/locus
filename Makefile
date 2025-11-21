.PHONY: help install install-uv install-dev install-mcp test lint format clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package with basic dependencies (using pip)
	pip install -e .

install-uv: ## Install package with basic dependencies (using uv - faster!)
	uv pip install --system -e .

install-dev: ## Install package with dev dependencies (using uv - recommended for development)
	uv pip install --system -e .[dev]

install-dev-pip: ## Install package with dev dependencies (using pip)
	pip install -e .[dev]

install-mcp: ## Install package with MCP dependencies (heavy ML libs)
	uv pip install --system -e .[mcp]

test: ## Run tests (excluding MCP tests)
	python -m pytest tests/ --ignore=tests/mcp -q

test-all: ## Run all tests including MCP tests
	python -m pytest tests/ -q

test-verbose: ## Run tests with verbose output
	python -m pytest tests/ --ignore=tests/mcp -xvs

lint: ## Run ruff linter
	ruff check src/ tests/

lint-fix: ## Run ruff linter with auto-fix
	ruff check --fix src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/

format-check: ## Check code formatting without modifying
	ruff format --check src/ tests/

quality: lint-fix format test ## Run all quality checks (lint, format, test)

clean: ## Clean up cache and build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

uninstall: ## Uninstall the package
	pip uninstall -y locus-analyzer

reinstall: uninstall install-dev ## Uninstall and reinstall with dev dependencies
