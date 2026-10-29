.PHONY: install fmt lint typecheck test check dev migrate openapi openapi-check

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
openapi:
	uv run analyser-api export-openapi
openapi-check:
	uv run analyser-api export-openapi --check
check: lint typecheck test openapi-check
dev:
	uv run uvicorn --factory analyser_api.app:create_app --reload
migrate:
	uv run analyser-api migrate
