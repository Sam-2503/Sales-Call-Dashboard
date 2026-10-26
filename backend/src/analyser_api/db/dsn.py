"""Normalize provider PostgreSQL URLs for asyncpg and Alembic."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def asyncpg_dsn(value: str) -> str:
    """Convert a PostgreSQL provider URL to a SQLAlchemy asyncpg URL."""

    parsed = urlsplit(value)
    if parsed.scheme not in {"postgresql", "postgres", "postgresql+asyncpg"}:
        raise ValueError("database URL must use the PostgreSQL scheme")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode and sslmode != "disable":
        query["ssl"] = "require"
    return urlunsplit(
        ("postgresql+asyncpg", parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )
