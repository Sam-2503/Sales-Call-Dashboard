---
title: Sales Call Analyser
emoji: 📞
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Sales Call Analyser

This Space runs the FastAPI backend and serves the React build from the same
origin. The backend makes no LLM calls of its own; it runs the `call_analyser`
package against uploaded cold calls.

## Space secrets

Configure these in **Settings → Secrets** (never commit them):

- `DATABASE_URL` — Neon pooled PostgreSQL DSN.
- `DATABASE_URL_DIRECT` — Neon direct DSN, used by `alembic` at container start.
- `JWT_SECRET` — at least 32 random characters.
- `XAI_API_KEY` — the xAI secret used for Grok analysis and transcription.
- `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`,
  `S3_SECRET_ACCESS_KEY`, `S3_REGION` — private S3-compatible storage.
- `PLAYBOOK_ARTIFACT_PREFIX` — private prefix containing `latest.json` and the
  Chroma tarball.
- `ADMIN_TOKEN` — optional, enables the operator endpoints.

## Assumptions

- Docker Spaces expose one HTTP port; `PORT=7860` and `app_port: 7860` match.
- The container runs as uid 1000; `/app/data` and `/app/static` are writable
  only where the app needs them.
- Space disk is ephemeral. Audio lives in S3, and the Chroma directory is
  restored from the private artifact at startup; it is never rebuilt per call.
- Set `FAKE_MODE=true` only for an offline demo; live analysis needs xAI.
