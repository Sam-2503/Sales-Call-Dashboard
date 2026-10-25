.PHONY: install fmt lint typecheck check backend-check check-all

install:
	uv sync --extra dev
fmt:
	uv run ruff format src
lint:
	uv run ruff check src
typecheck:
	uv run mypy src
check: lint typecheck
backend-check:
	$(MAKE) -C backend check
check-all: check backend-check
