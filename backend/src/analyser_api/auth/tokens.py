"""Short-lived HS256 workspace tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from analyser_api.config import Settings

ALGORITHM = "HS256"
TOKEN_TYPE = "workspace"
TOKEN_TTL_S = 30 * 24 * 3600


def issue_token(workspace_id: UUID, settings: Settings, ttl_s: int = TOKEN_TTL_S) -> str:
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is required to issue workspace tokens")
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(workspace_id),
            "typ": TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(seconds=ttl_s),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def verify_token(token: str, settings: Settings) -> UUID:
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET is not configured")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("typ") != TOKEN_TYPE:
        raise ValueError("invalid token type")
    try:
        return UUID(str(payload["sub"]))
    except (KeyError, ValueError) as error:
        raise ValueError("invalid workspace token subject") from error
