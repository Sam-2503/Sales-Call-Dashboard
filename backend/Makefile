.PHONY: install fmt lint typecheck check dev worker seed-demo openapi openapi-check

install:
	uv sync --extra dev
fmt:
	uv run ruff format src
lint:
	uv run ruff check src
typecheck:
	uv run mypy src
openapi:
	uv run analyser-api export-openapi
openapi-check:
	uv run analyser-api export-openapi --check
check: lint typecheck openapi-check
dev:
	uv run uvicorn --factory analyser_api.app:create_app --reload
worker:
	uv run analyser-api worker
seed-demo:
	uv run analyser-api seed-demo
