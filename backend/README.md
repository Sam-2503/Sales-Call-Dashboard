# Call Analyser API

FastAPI service for consent-based cold-call analysis. It owns uploads,
authentication, durable jobs, storage, reports, SQL trends, feedback, quotas,
retention, and the operator surface. Analysis behaviour stays in the `call_analyser` package under `src/`; this
service makes **no LLM calls of its own**.

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
```

- **Postgres is the queue.** `jobs` and `job_events` survive restarts; claims
  use `FOR UPDATE SKIP LOCKED`.
- **The stage cache is per call.** A retried job skips completed package stages.
- **The worker never holds a database transaction across a pipeline run.**

## Quickstart (under 5 minutes, fake mode)

Requirements: PostgreSQL, `uv`, Python 3.11+, and the
`ffmpeg` package (which provides both `ffmpeg` and `ffprobe`).

On macOS, install it with:

```bash
brew install ffmpeg
```

```bash
cd backend
cp .env.example .env
# Set DATABASE_URL to postgresql://postgres:postgres@localhost:5432/analyser
# Set an arbitrary 32+ character JWT_SECRET and FAKE_MODE=true in .env.
make install
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
produce an `insufficient_data` report. Live calls need `GROQ_API_KEY`; analysis
uses the active rubric, with the bundled sales rubric as the default.

## Commands

```bash
make install       # uv sync --extra dev
make fmt           # ruff format src
make lint          # ruff check src
make typecheck     # strict mypy over src
make openapi       # write backend/openapi.json
make check         # lint + mypy + OpenAPI drift
make dev           # uvicorn factory
make worker        # standalone worker process
make seed-demo
```

Run `make check` from this directory for the same check.

## Configuration

Every value is read from environment variables or `.env`; see
[`.env.example`](.env.example). Package tunables are composed as
`Settings.package` and are read by `call_analyser` too.

| Group | Main variables / defaults |
|---|---|
| Runtime | `ENVIRONMENT=dev`, `HOST=0.0.0.0`, `PORT=7860`, `LOG_LEVEL=INFO`, `CORS_ORIGINS=[]`, `TRUSTED_PROXY_COUNT=1`, `STATIC_DIR` |
| Database | `DATABASE_URL`, `DB_POOLER=true`, `DB_POOL_SIZE=5`, `DB_CONNECT_RETRIES=3` |
| Auth | `JWT_SECRET` (required outside dev, 32+ chars), `JWT_TTL_DAYS=30`, `MEDIA_TOKEN_TTL_S=600` |
| Abuse limits | `WORKSPACE_RATE_LIMIT_PER_HOUR=20`, `UPLOAD_RATE_LIMIT_PER_HOUR=30`, `DAILY_CALLS_PER_WORKSPACE=10`, `DAILY_CALLS_GLOBAL=100`, `DAILY_BUDGET_USD=1.00` |
| Uploads | `MAX_UPLOAD_MB=25`, `ALLOWED_AUDIO_EXTENSIONS`, `MAX_REANALYSES_PER_CALL=3` |
| Storage | `STORAGE_BACKEND=local`, `STORAGE_DIR`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, private keys |
| Worker | `WORKER_ENABLED=true`, `WORKER_MODE=thread`, `WORKER_CONCURRENCY=2`, `JOB_MAX_ATTEMPTS=2`, `JOB_STALE_S=60`, `SHUTDOWN_GRACE_S=20` |
| SSE | `SSE_POLL_S=0.7`, `SSE_KEEPALIVE_S=15` |
| Retention | `RETENTION_DAYS=30`, `WORKSPACE_IDLE_DAYS=60`, `DEMO_IDLE_DAYS=3`, `JANITOR_INTERVAL_S=3600` |
| Demo/trends | `DEMO_SEED_CALLS=8`, `DEMO_WORKSPACES_PER_IP_PER_DAY=3`, `TRENDS_MIN_CALLS=3` |
| Analysis | `RUBRIC_PATH`, `FAKE_MODE`; uploaded YAML rubrics override the default per call |

Admin: `ADMIN_TOKEN` is unset by default; admin endpoints return 404 until it
is configured.

## Deployment

### Neon

Use the **pooled** Neon connection string in `DATABASE_URL` and set
`DB_POOLER=true`; the engine disables prepared-statement caches for pooled
connections. Keep Neon’s query parameters, including `sslmode=require`.

For deployment, create the required tables in Neon, then set `ENVIRONMENT=prod`,
`DATABASE_URL`, `DB_POOLER=true`, a `JWT_SECRET` of at least 32 random
characters, and `GROQ_API_KEY` before starting the service.

### S3-compatible storage

Set `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, and
credentials. Audio keys are `{workspace_id}/{call_id}/original.{ext}`; the
client filename is never used as a key. The bucket stays private; media is
streamed through the API with a short-lived signed token.

For Hugging Face Spaces, do not rely on `STORAGE_BACKEND=local`: the Space
filesystem is ephemeral. Neon Object Storage exposes an S3-compatible
endpoint, so the existing adapter can use the `call-recordings` bucket:

```dotenv
STORAGE_BACKEND=s3
S3_BUCKET=call-recordings
AWS_ENDPOINT_URL=<neon-storage-endpoint>
AWS_REGION=<neon-region>
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
```

Copy the endpoint, region, access key, and secret shown by Neon in the Object
Storage `.env` tab. The endpoint is required; without it boto3 contacts AWS
instead of Neon and readiness fails with a 403. The backend accepts both these
standard `AWS_*` names and the `S3_*` names.
The bucket credentials need object `Get`, `Put`, `Delete`, `Head`, and
prefix-list access. Keep the bucket private; the API serves short-lived
authenticated media URLs. The backend's existing `S3Storage` implementation
handles upload, range reads for audio playback, deletion, and health checks.

### JWT secret

Generate it locally and store it only in `.env` or the deployment secret store:

```bash
openssl rand -base64 48
```

Set the output as `JWT_SECRET`. Production rejects missing or
shorter-than-32-character secrets. Changing it invalidates existing workspace
tokens.

### Groq and rubric configuration

Set `GROQ_API_KEY` as a backend/deployment secret. It is read by the
`call_analyser` package and never sent to the browser. The bundled
`call_analyser/rubric/sales_v1.yaml` is used by default. Operators can point
`RUBRIC_PATH` at another validated rubric file for company-wide guidance.
The website upload form can also attach a validated YAML checklist to an
individual call; it is stored with that queued job and overrides the default
for that run.

## Operations

- **Seeding:** `analyser-api seed-demo --calls 12` reuses the fixed `demo-seed`
  label, so repeated runs are idempotent. `POST /api/v1/workspaces/demo` creates
  a fresh independent demo workspace.
- **Retention:** the janitor deletes non-demo calls older than
  `RETENTION_DAYS`, idle non-demo workspaces, and idle demo workspaces. It
  deletes stored audio prefixes too and logs/retries failures.
- **Admin:** `GET /api/v1/admin/stats` and `GET /api/v1/admin/feedback.jsonl`
  require `X-Admin-Token`; both are 404 when `ADMIN_TOKEN` is unset.
- **Readiness:** `GET /readyz` checks database, rubric, and storage. It makes no
  paid calls.
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
- Generate TypeScript types from [`openapi.json`](openapi.json), the backend API
  contract.
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
  Hugging Face behaviour cannot be fully verified locally.
- The package's `fixtures/reports/full_report.json` is absent in this checkout;
  demo data is generated from the active rubric instead.
