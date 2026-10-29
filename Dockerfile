# --- frontend build (placeholder until the React prompt lands) -----------------
FROM node:20-alpine AS frontend
WORKDIR /src
COPY . .
RUN if [ -f frontend/package.json ]; then \
      cd frontend && npm ci && npm run build && cp -R dist /dist; \
    else \
      mkdir -p /dist && printf '<!doctype html><title>Call Analyser</title>' > /dist/index.html; \
    fi

# --- Python runtime -------------------------------------------------------------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    STATIC_DIR=/app/static \
    RUBRIC_PATH=/app/rubrics/sales_v1.yaml \
    CHROMA_PATH=/app/data/chroma \
    STORAGE_DIR=/app/data/audio \
    WORK_DIR=/app/data/work \
    UV_LINK_MODE=copy
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md AGENTS.md ./
COPY src ./src
COPY rubrics ./rubrics
COPY schemas ./schemas
COPY backend ./backend
RUN cd backend && uv sync --frozen --no-dev

COPY --from=frontend /dist ./static
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/data/chroma /app/data/audio /app/data/work \
    && chown -R app:app /app
USER app
WORKDIR /app/backend
ENV PATH="/app/backend/.venv/bin:${PATH}"
EXPOSE 7860
CMD ["sh", "-c", "analyser-api migrate && analyser-api serve"]
