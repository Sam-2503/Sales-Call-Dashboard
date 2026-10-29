import json

from analyser_api.openapi import OPENAPI_PATH, render_openapi


def test_committed_openapi_is_current() -> None:
    assert OPENAPI_PATH.read_text(encoding="utf-8") == render_openapi()


def test_operation_ids_are_clean_and_stable() -> None:
    schema = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    operation_ids = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert "createCall" in operation_ids
    assert "createWorkspace" in operation_ids
    assert "healthz" in operation_ids
    assert all(operation_id.isalnum() for operation_id in operation_ids)
