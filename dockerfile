FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR $HOME/app

COPY --chown=user backend/ ./backend/
WORKDIR $HOME/app/backend
RUN uv sync --frozen --no-dev
COPY --chown=user --from=frontend /build/dist $HOME/app/frontend/dist

ENV STATIC_DIR=/home/user/app/frontend/dist
EXPOSE 7860
CMD ["uv", "run", "--no-dev", "analyser-api", "serve"]
