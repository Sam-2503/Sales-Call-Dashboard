.PHONY: install fmt lint typecheck check

install:
	uv sync --extra dev
fmt:
	uv run ruff format src
lint:
	uv run ruff check src
typecheck:
	uv run mypy src
check: lint typecheck
