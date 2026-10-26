# Analyser API

The backend uses Neon PostgreSQL:

- `DATABASE_URL` is the Neon pooled connection string used by the API and worker.
- `DATABASE_URL_DIRECT` is the Neon direct connection string used for Alembic migrations.
- `DB_POOLER=true` disables asyncpg prepared-statement caches for Neon's transaction pooler.

Copy `.env.example` to `.env`, replace both Neon URLs with values from the Neon
Connect dialog, set a random `JWT_SECRET` with at least 32 characters, then run:

```bash
uv sync --extra dev
make migrate
make dev
```

The health endpoint is available at `http://localhost:8000/healthz`.
