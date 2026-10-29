# Call Analyser API

FastAPI service for consent-based cold-call analysis. It owns uploads,
authentication, durable jobs, storage, reports, SQL trends, feedback, quotas,
retention, and the operator surface. Analysis behaviour stays in the
`call_analyser` package; this service makes **no LLM calls of its own**.

## Architecture

```mermaid
flowchart LR
  UI[React build / same origin] -->|Bearer + multipart| API[FastAPI /api/v1]
  API --> DB[(Neon Postgres)]
  API --> AUDIO[(S3-compatible audio)]
  API -->|queued job| DB
  WORKER[Worker thread or process] -->|FOR UPDATE SKIP LOCKED| DB
  WORKER -->|one pipeline run| PKG[call_analyser.stream_analysis]
  PKG -->|events| DB
  PKG -->|CallReport| WORKER
  WORKER -->|reports + derived rows| DB
  API -->|SQL| TRENDS[Trends / benchmarks]
  CHROMA[(read-only Chroma artifact)] --> PKG
```

- **Postgres is the queue.** `jobs` and `job_events` survive restarts; claims
  use `FOR UPDATE SKIP LOCKED`.
- **The stage cache is per call.** A retried job skips completed package stages.
- **The worker never holds a database transaction across a pipeline run.**
- **The playbook is never indexed during a request.** It is published once to a
  private bucket and synced at startup; sync makes zero embedding calls.

## Quickstart (under 5 minutes, fake mode)

Requirements: Docker (or a local PostgreSQL), `uv`, Python 3.11+, `ffmpeg`.

```bash
docker compose up -d postgres
cd backend
cp .env.example .env
# Set DATABASE_URL to postgresql://postgres:postgres@localhost:5432/analyser
# Set an arbitrary 32+ character JWT_SECRET and FAKE_MODE=true in .env.
make install
make migrate
make dev
```

In another terminal:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/workspaces | tee /tmp/ws.json
TOKEN=$(python3 -c 'import json;print(json.load(open("/tmp/ws.json"))["token"])')

# Any short audio file works; this creates a ~65 s tone without committing audio.
ffmpeg -f lavfi -i "sine=frequency=440:duration=65" -ar 16000 /tmp/sample.wav
curl -s -H "Authorization: Bearer $TOKEN" \
  -F file=@/tmp/sample.wav -F consent=true \
  -F title="Quickstart call" \
  http://127.0.0.1:8000/api/v1/calls | tee /tmp/upload.json

CALL=$(python3 -c 'import json;print(json.load(open("/tmp/upload.json"))["call_id"])')
JOB=$(python3 -c 'import json;print(json.load(open("/tmp/upload.json"))["job_id"])')
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/jobs/$JOB
curl -N -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/jobs/$JOB/events
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/calls/$CALL/report
```

Seed deterministic demo data (no LLM cost), then use the printed token:

```bash
make seed-demo
# or: uv run analyser-api seed-demo --calls 12
```

`FAKE_MODE=true` uses the scripted package runner, so uploads work offline and
produce an `insufficient_data` report. Live calls need `GEMINI_API_KEY` and a
published/readable playbook index.

## Commands

```bash
make install       # uv sync --extra dev
make fmt           # ruff format src tests
make lint          # ruff check src tests
make typecheck     # strict mypy over src
make test          # pytest; db tests skip loudly without Postgres
make openapi       # write backend/openapi.json
make check         # lint + mypy + tests + OpenAPI drift
make migrate       # alembic upgrade head
make dev           # uvicorn factory
make worker        # standalone worker process
make seed-demo
```

Run `make backend-check` from the repository root for the same check. The
`db`-marked tests require a real PostgreSQL; set `TEST_DATABASE_URL` or install
local `initdb`/`pg_ctl`. Without either they are skipped and reported.

## Configuration

Every value is read from environment variables or `.env`; see
[`.env.example`](.env.example). Package tunables are composed as
`Settings.package` and are read by `call_analyser` too.

| Group | Main variables / defaults |
|---|---|
| Runtime | `ENVIRONMENT=dev`, `HOST=0.0.0.0`, `PORT=7860`, `LOG_LEVEL=INFO`, `CORS_ORIGINS=[]`, `TRUSTED_PROXY_COUNT=1`, `STATIC_DIR` |
| Database | `DATABASE_URL`, `DATABASE_URL_DIRECT`, `DB_POOLER=true`, `DB_POOL_SIZE=5`, `DB_CONNECT_RETRIES=3` |
| Auth | `JWT_SECRET` (required outside dev, 32+ chars), `JWT_TTL_DAYS=30`, `MEDIA_TOKEN_TTL_S=600` |
| Abuse limits | `WORKSPACE_RATE_LIMIT_PER_HOUR=20`, `UPLOAD_RATE_LIMIT_PER_HOUR=30`, `DAILY_CALLS_PER_WORKSPACE=5`, `DAILY_CALLS_GLOBAL=100`, `DAILY_BUDGET_USD=1.00` |
| Uploads | `MAX_UPLOAD_MB=25`, `ALLOWED_AUDIO_EXTENSIONS`, `MAX_REANALYSES_PER_CALL=3` |
| Storage | `STORAGE_BACKEND=local`, `STORAGE_DIR`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, private keys |
| Worker | `WORKER_ENABLED=true`, `WORKER_MODE=thread`, `WORKER_CONCURRENCY=2`, `JOB_MAX_ATTEMPTS=2`, `JOB_STALE_S=60`, `SHUTDOWN_GRACE_S=20` |
| SSE | `SSE_POLL_S=0.7`, `SSE_KEEPALIVE_S=15` |
| Retention | `RETENTION_DAYS=30`, `WORKSPACE_IDLE_DAYS=60`, `DEMO_IDLE_DAYS=3`, `JANITOR_INTERVAL_S=3600` |
| Demo/trends | `DEMO_SEED_CALLS=8`, `DEMO_WORKSPACES_PER_IP_PER_DAY=3`, `TRENDS_MIN_CALLS=3` |
| Analysis | `RUBRIC_PATH`, `PLAYBOOK_PATH`, `CHROMA_PATH`, `PLAYBOOK_ARTIFACT_PREFIX`, `FAKE_MODE`, `PLAYBOOK_GROUNDING` |

Admin: `ADMIN_TOKEN` is unset by default; admin endpoints return 404 until it
is configured.

## Deployment

### Neon

Use the **pooled** host in `DATABASE_URL` and the **direct** host in
`DATABASE_URL_DIRECT`. Set `DB_POOLER=true` for transaction pooling; the engine
disables prepared-statement caches. `analyser-api migrate` uses the direct DSN.

### S3-compatible storage

Set `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, and
credentials. Audio keys are `{workspace_id}/{call_id}/original.{ext}`; the
client filename is never used as a key. The bucket stays private; media is
streamed through the API with a short-lived signed token.

### Playbook artifact

The Chroma index contains copyrighted book text. Keep it in a **private**
bucket and never in git.

```bash
uv run analyser-api playbook publish   # refuses an incomplete manifest
uv run analyser-api playbook sync      # startup also calls this when prefix is set
```

Publish packs the Chroma directory plus its manifest, uploads it under
`PLAYBOOK_ARTIFACT_PREFIX`, and records `latest.json` with a sha256 and manifest
summary. Sync compares PDF sha256/chunker/embedding model/dimension, downloads,
verifies the checksum, swaps atomically, and validates with
`PlaybookIndex.open`. It never embeds.

### Hugging Face Space

Use the Docker Space template in [`deploy/space_README.md`](../deploy/space_README.md).
Set the secrets listed there. The container runs as uid 1000 and serves the
React build from `STATIC_DIR` with an SPA fallback; `/api`, `/healthz` and
`/readyz` are never shadowed.

## Operations

- **Migrations:** `analyser-api migrate` (direct DSN). Start the container with
  migrate then serve.
- **Seeding:** `analyser-api seed-demo --calls 12` reuses the fixed `demo-seed`
  label, so repeated runs are idempotent. `POST /api/v1/workspaces/demo` creates
  a fresh independent demo workspace.
- **Retention:** the janitor deletes non-demo calls older than
  `RETENTION_DAYS`, idle non-demo workspaces, and idle demo workspaces. It
  deletes stored audio prefixes too and logs/retries failures.
- **Admin:** `GET /api/v1/admin/stats` and `GET /api/v1/admin/feedback.jsonl`
  require `X-Admin-Token`; both are 404 when `ADMIN_TOKEN` is unset.
- **Readiness:** `GET /readyz` checks database, rubric, storage, and the playbook
  index. It makes no paid calls. A failed artifact sync leaves readiness failed
  and prevents the worker from starting.
- **Contract:** `make openapi` writes deterministic sorted JSON with stable
  operation IDs; `make check` fails on drift.

## Frontend contract

- Send `Authorization: Bearer <token>` on every API call except `/healthz`,
  `/readyz`, and `/meta`.
- **SSE must use a fetch-based client**, because `EventSource` cannot set an
  Authorization header. Fall back to polling `GET /api/v1/jobs/{id}`.
- Audio playback uses `GET /api/v1/calls/{id}/audio-url`, then the returned
  signed same-origin media URL. It supports HTTP Range.
- Handle `report_status` (`ok` | `insufficient_data`) and `available: false`
  with a reason for trends/weak spots/benchmarks. Never render fabricated data.
- Generate TypeScript types from [`openapi.json`](openapi.json) and the shared
  [`call_report.schema.json`](../schemas/call_report.schema.json).
- Reports are served with `Cache-Control: no-store`; they never include the
  package `debug` section.

## Privacy and consent

The upload form must send `consent=true`; the timestamp is stored. Audio and
reports are personal data. They are scoped to a workspace, served no-store,
deleted with the call or workspace (including audio objects), and automatically
removed by retention. Logs never contain transcripts, audio text, request
bodies, tokens, or query strings. Operator feedback export excludes demo
workspaces and never includes transcript text. Anonymous users who lose their
token lose access; there are no accounts or password recovery.

## Limitations

- Anonymous bearer workspaces; this is not an account system.
- Single-process rate limiting (per IP); quotas and retention are durable.
- One worker process/thread is assumed for fair queue ordering; claims are safe
  across processes, but this is not a multi-region deployment.
- Free-tier cold starts and SSE behind proxies can add latency; keepalives are
  emitted.
- Cost figures are estimates from package usage metadata; they are not billing.
- `db` tests are skipped when no PostgreSQL is available, and Docker/Neon/S3/
  Hugging Face behaviour cannot be fully verified locally.
- The package's `fixtures/reports/full_report.json` is absent in this checkout;
  demo data is generated from the active rubric instead.
