---
title: Sales Call Analyser
sdk: docker
app_port: 7860
---

# Sales Call Analyser

An evidence-backed dashboard for reviewing sales-call recordings. A user
uploads a call and optionally a company rubric; the app transcribes the audio,
checks the conversation against that rubric, and shows scores, verified quotes,
timestamps, coaching, trends, and a suggested follow-up message.

## How it works

1. The React frontend uploads audio and optional YAML company guidelines.
2. FastAPI validates consent, file limits, the rubric, and the workspace quota.
3. Audio is stored locally or in private S3-compatible storage, while
   PostgreSQL stores calls, jobs, events, reports, and feedback.
4. A worker claims the durable job and runs the `call_analyser` pipeline.
5. Groq Whisper transcribes the call; deterministic code computes metrics.
6. LangChain and Groq evaluate the transcript against the active rubric.
7. Evidence is matched to transcript turns, unverified findings are removed,
   and a `CallReport` is saved for the frontend.

The default rubric is
[`backend/src/call_analyser/rubric/sales_v1.yaml`](backend/src/call_analyser/rubric/sales_v1.yaml).
An uploaded rubric must follow the same YAML/Pydantic shape: `id`, `version`,
`name`, weighted `categories`, and `items` with `category`, `title`,
`description`, and `good_looks_like`. Category weights must total `1.0`.

## Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind, React Router, TanStack
  Query, Radix UI, native audio, and OpenAPI-generated types.
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy async, PostgreSQL/Neon,
  `uv`, and a durable PostgreSQL-backed worker queue.
- **AI:** Groq Whisper (`whisper-large-v3-turbo`) for transcription and Groq
  chat through LangChain (`openai/gpt-oss-20b`) for report analysis.
- **Storage:** local disk for development or private S3-compatible storage
  such as Neon Object Storage in deployment.

## Run locally

Requirements: Python 3.11+, `uv`, Node 20.19+, `ffmpeg`/`ffprobe`, and a
PostgreSQL database. On macOS:

```bash
brew install ffmpeg
```

Create the database tables from the SQLAlchemy models in
[`backend/src/analyser_api/db/models.py`](backend/src/analyser_api/db/models.py).
Then configure the backend:

```bash
cd backend
cp .env.example .env
# Set DATABASE_URL and JWT_SECRET.
# Set FAKE_MODE=true for an offline demo, or add GROQ_API_KEY for live analysis.
make install
make dev
```

Build the frontend separately:

```bash
cd frontend
npm ci
npm run build
```

For production, set `ENVIRONMENT=prod`, use a pooled Neon
`DATABASE_URL`, a random 32+ character `JWT_SECRET`, `GROQ_API_KEY`, and
private S3 credentials. Build `frontend/dist`, set the backend static directory
to it, and run:

```bash
cd backend
uv run uvicorn --factory analyser_api.app:create_app --host 0.0.0.0 --port 7860
```

Keep the worker enabled. The backend requires `ffmpeg` and `ffprobe` for audio
validation and normalization.

## API

All application routes are under `/api/v1` and require the workspace bearer
token unless noted. Create a workspace first with `POST /workspaces`.

| Area          | Endpoints                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------- |
| Workspace     | `POST /workspaces`, `POST /workspaces/demo`, `GET /me`, `DELETE /me`                               |
| Calls         | `POST /calls`, `GET /calls`, `GET /calls/{id}`, `DELETE /calls/{id}`, `POST /calls/{id}/reanalyse` |
| Jobs          | `GET /jobs/{id}`, `GET /jobs/{id}/events`, retry/cancel call jobs                                  |
| Reports/media | `GET /calls/{id}/report`, `GET /calls/{id}/audio-url`, `GET /media/audio`                          |
| Feedback      | `GET /calls/{id}/feedback`, `PUT/DELETE /calls/{id}/feedback/{finding_id}`                         |
| Rubric/meta   | `GET /rubric`, `GET /meta`                                                                         |
| Progress      | `GET /trends/scores`, `GET /trends/weak-spots`, `GET /benchmarks`                                  |
| Agents        | `GET/POST /agents`, `PATCH /agents/{id}`                                                           |

Unauthenticated operational routes are `/healthz` and `/readyz`. The complete
request/response contract is the committed
[`backend/openapi.json`](backend/openapi.json), and generated frontend types
are in [`frontend/src/api/schema.d.ts`](frontend/src/api/schema.d.ts).

## Report and data model

The report contract is defined by the Pydantic models in
[`backend/src/call_analyser/schemas`](backend/src/call_analyser/schemas):
status and metadata, transcript, scorecard, audio metrics, rubric results,
missed moments, customer signals, next steps, coaching, and warnings. Every
finding may include a transcript quote, speaker, and clickable approximate
timestamps. Reports never expose the internal debug section.

The database models are in
[`backend/src/analyser_api/db/models.py`](backend/src/analyser_api/db/models.py).
They cover workspaces, agents, calls, jobs, job events, reports, category/item
results, findings, feedback, and per-call stage cache. Create and maintain
these tables directly in Neon; this project intentionally has no migration
tool.

## Checks

```bash
cd backend && make check       # Ruff, strict mypy, OpenAPI drift
cd frontend && npm run check  # TypeScript and production build
```

Audio, transcripts, and reports are private workspace data. Do not commit
`.env`, recordings, credentials, or generated storage data.
