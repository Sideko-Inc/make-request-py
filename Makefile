.PHONY: help test lint format release-patch release-minor release-major

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test:  ## Run tests
	poetry run pytest

test-cov:  ## Run tests with coverage
	poetry run pytest --cov=make_request --cov-report=term-missing

lint:  ## Run linting
	poetry run ruff check .
	poetry run black --check .

format:  ## Format code
	poetry run black .
	poetry run ruff check --fix .

typecheck:  ## Run type checking
	poetry run mypy .

release-patch:  ## Release patch version (1.0.0 -> 1.0.1)
	python3 scripts/release.py patch

release-minor:  ## Release minor version (1.0.0 -> 1.1.0)
	python3 scripts/release.py minor

release-major:  ## Release major version (1.0.0 -> 2.0.0)
	python3 scripts/release.py major

install:  ## Install dependencies
	poetry install

build:  ## Build package
	poetry build

clean:  ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete