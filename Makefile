PROJECT_DIR = $(shell pwd)

# Сокет контейнерного движка: переопределяется переменной окружения DOCKER_HOST
RUNTIME_DIR = $(or $(XDG_RUNTIME_DIR),/run/user/$(shell id -u))
DOCKER_HOST ?= unix://$(RUNTIME_DIR)/podman/podman.sock
TESTCONTAINERS_RYUK_DISABLED ?= true
export DOCKER_HOST
export TESTCONTAINERS_RYUK_DISABLED

# Без --all-extras uv собирает окружение без драйверов БД: они нужны mypy и сбору тестов
UV_RUN = uv run --all-extras

.PHONY: default
default: format lint test-fast

.PHONY: rules-check
rules-check:
	$(UV_RUN) python scripts/rules_lint.py

.PHONY: lint
lint: rules-check
	$(UV_RUN) mypy
	$(UV_RUN) ruff format --check .
	$(UV_RUN) ruff check .

.PHONY: format
format:
	$(UV_RUN) ruff format .
	$(UV_RUN) ruff check --fix .

.PHONY: test
test:
	$(UV_RUN) tox -p auto

.PHONY: test-fast
test-fast:
	$(UV_RUN) pytest -m "not integration"

.PHONY: test-integration
test-integration:
	$(UV_RUN) pytest -m integration

.PHONY: cover
cover:
	$(UV_RUN) pytest --cov=pytrm --cov-report=term-missing --cov-report=html

.PHONY: build
build:
	uv build
