from uuid import uuid4

import pytest
import jwt

from analyser_api.auth.tokens import issue_token, verify_token
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
