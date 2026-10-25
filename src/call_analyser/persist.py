"""Small, swappable success-only cache for expensive analysis stages."""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast, get_type_hints, runtime_checkable

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class StageStore(Protocol):
    async def get(self, key: str) -> dict[str, Any] | None: ...
    async def put(self, key: str, value: dict[str, Any]) -> None: ...


class InMemoryStageStore:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        return self.values.get(key)

    async def put(self, key: str, value: dict[str, Any]) -> None:
        self.values[key] = value


class JsonFileStageStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    async def get(self, key: str) -> dict[str, Any] | None:
        path = self.directory / f"{key}.json"
        if not path.exists():
            return None
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    async def put(self, key: str, value: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{key}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        temporary.replace(path)


def _cache_key(stage: str, input_value: BaseModel, config: RunnableConfig) -> str:
    configurable = config.get("configurable", {})
    payload = {
        "stage": stage,
        "schema_version": configurable.get("schema_version", "1.0"),
        "prompt_ids": configurable.get("prompt_ids", {}),
        "model_ids": configurable.get("model_ids", {}),
        "input": input_value.model_dump(mode="json"),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def persisted(stage: str) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Cache a Pydantic stage result when its Runnable config provides a store."""

    def decorator(function: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        output_model = get_type_hints(function).get("return")
        if not inspect.isclass(output_model) or not issubclass(output_model, BaseModel):
            raise TypeError("persisted stages must return a Pydantic model")

        @functools.wraps(function)
        async def wrapper(input_value: BaseModel, config: RunnableConfig, **kwargs: Any) -> T:
            configurable = config.get("configurable", {})
            store = configurable.get("stage_store")
            if store is None or configurable.get("force_refresh", False):
                return await function(input_value, config, **kwargs)
            if not isinstance(store, StageStore):
                raise TypeError("configurable.stage_store must implement StageStore")
            key = _cache_key(stage, input_value, config)
            cached = await store.get(key)
            if cached is not None:
                return cast(T, output_model.model_validate(cached))
            result = await function(input_value, config, **kwargs)
            await store.put(key, result.model_dump(mode="json"))
            return result

        return wrapper

    return decorator
