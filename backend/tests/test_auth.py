from uuid import uuid4

import jwt
import pytest

from analyser_api.auth.tokens import (
    issue_media_token,
    issue_token,
    verify_media_token,
    verify_token,
)
from analyser_api.config import Settings


def test_workspace_token_round_trip() -> None:
    settings = Settings(jwt_secret="x" * 32)
    workspace_id = uuid4()
    assert verify_token(issue_token(workspace_id, settings), settings) == workspace_id


def test_workspace_token_rejects_wrong_secret() -> None:
    workspace_id = uuid4()
    token = issue_token(workspace_id, Settings(jwt_secret="x" * 32))
    with pytest.raises(jwt.InvalidTokenError):
        verify_token(token, Settings(jwt_secret="y" * 32))


def test_media_token_is_bound_to_call_and_type() -> None:
    settings = Settings(jwt_secret="x" * 32)
    workspace_id = uuid4()
    call_id = uuid4()
    token = issue_media_token(workspace_id, call_id, settings)
    assert verify_media_token(token, call_id, settings) == workspace_id
    with pytest.raises(ValueError):
        verify_media_token(token, uuid4(), settings)
    with pytest.raises(ValueError):
        verify_token(token, settings)


def test_expired_workspace_token_is_rejected() -> None:
    settings = Settings(jwt_secret="x" * 32)
    token = issue_token(uuid4(), settings, ttl_s=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(token, settings)
