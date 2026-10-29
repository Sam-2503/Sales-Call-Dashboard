# Backend guidance

## Principles
- Keep HTTP, persistence, authentication, storage, quota, and queueing concerns here.
- Keep all pipeline behavior in `call_analyser`; import its public API only.
- Scope every database query by `workspace_id`; another workspace's id returns 404.
- Never log request bodies, tokens, query strings, transcripts, or audio-derived text.
- Treat reports and audio as personal data; no-store, consent, deletion, retention.
- No network or database connection while importing modules.
- No LLM calls from the backend.

## Commands
```bash
make install
make fmt
make lint
make typecheck
make test
make openapi
make check
make migrate
make dev
```

Every change ends with `make check` green, including the OpenAPI drift check.

## Layout
- `src/analyser_api/app.py`: `create_app` factory and middleware.
- `routers/`: thin HTTP aggregates; `services/`: application operations.
- `db/`: engine, DSN normalization, models. `auth/`: JWT and rate limits.
- `storage/`: local and S3 audio backends. `jobs/`: queue, worker, stage store.
- `tests/`: offline tests; PostgreSQL tests are marked `db`.

## Do not
- Do not edit `src/call_analyser` or import private package modules.
- Do not commit `.env`, audio, transcripts, Chroma data, or real book text.
- Do not hard-code secrets, hosts, limits, or prices.
- Do not add Redis, Celery, pgvector, LangGraph, or another LLM client.
- Do not block the event loop with synchronous I/O or subprocesses.
