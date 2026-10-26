# Analyser API

The backend uses Neon PostgreSQL:

- `DATABASE_URL` is the single Neon connection string used by the API, worker,
  and Alembic migrations.
- `DB_POOLER=true` disables asyncpg prepared-statement caches when the Neon
  connection uses a transaction pooler.

Copy `.env.example` to `.env`, replace `DATABASE_URL` with the connection
string from the Neon Connect dialog, set a random `JWT_SECRET` with at least
32 characters, then run:

```bash
uv sync --extra dev
make migrate
make dev
```

The health endpoint is available at `http://localhost:8000/healthz`.
