PROJECT_DIR = $(shell pwd)

# Сокет контейнерного движка: переопределяется переменной окружения DOCKER_HOST
RUNTIME_DIR = $(or $(XDG_RUNTIME_DIR),/run/user/$(shell id -u))
DOCKER_HOST ?= unix://$(RUNTIME_DIR)/podman/podman.sock
TESTCONTAINERS_RYUK_DISABLED ?= true
export DOCKER_HOST
export TESTCONTAINERS_RYUK_DISABLED

.PHONY: default
default: format lint test-fast

.PHONY: rules-check
rules-check:
	uv run python scripts/rules_lint.py

.PHONY: lint
lint: rules-check
	uv run mypy
	uv run ruff format --check .
	uv run ruff check .

.PHONY: format
format:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: test
test:
	uv run tox -p auto

.PHONY: test-fast
test-fast:
	uv run pytest -m "not integration"

.PHONY: test-integration
test-integration:
	uv run pytest -m integration

.PHONY: cover
cover:
	uv run pytest --cov=pytrm --cov-report=term-missing --cov-report=html

.PHONY: build
build:
	uv build
