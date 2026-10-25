.PHONY: install fmt lint typecheck test check dev migrate

install:
	uv sync --extra dev
fmt:
	uv run ruff format src
lint:
	uv run ruff check src
typecheck:
	uv run mypy src
test:
	uv run pytest
check: lint typecheck test
dev:
	uv run uvicorn analyser_api.app:app --reload
migrate:
	uv run analyser-api migrate
