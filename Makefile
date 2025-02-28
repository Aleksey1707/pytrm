PROJECT_DIR = $(shell pwd)

.PHONY: lint
lint:
	pre-commit run -a

.PHONY: test
test:
	venv/bin/python -m tox

.PHONY: test-fast
test:
	venv/bin/python -m pytest