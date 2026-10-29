.PHONY: install fmt lint typecheck test check backend-check check-all

install:
	uv sync --extra dev
fmt:
	uv run ruff format src tests
lint:
	uv run ruff check src tests
typecheck:
	uv run mypy src
test:
	uv run pytest
check: lint typecheck test
backend-check:
	$(MAKE) -C backend check
check-all: check backend-check
