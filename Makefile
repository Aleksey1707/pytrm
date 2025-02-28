PROJECT_DIR = $(shell pwd)

.PHONY: lint
lint:
	pre-commit run -a

.PHONY: test
test:
	PYTHONPATH=. venv/bin/pytest