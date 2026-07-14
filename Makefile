PROJECT_DIR = $(shell pwd)

.PHONY: build
build:
	uv build

.PHONY: lint
lint:
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
	uv run pytest
