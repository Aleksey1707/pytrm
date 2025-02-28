PROJECT_DIR = $(shell pwd)

.PHONY: lint
lint:
	venv/bin/python -m mypy
	venv/bin/python -m black --check .
	venv/bin/python -m isort --check .
	venv/bin/python -m flake8

.PHONY: format
format:
	venv/bin/python -m black .
	venv/bin/python -m isort .
	venv/bin/python -m autoflake .

.PHONY: test
test:
	venv/bin/python -m tox

.PHONY: test-fast
test-fast:
	venv/bin/python -m pytest