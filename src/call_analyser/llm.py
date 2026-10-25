"""The sole Stage 2 boundary for constructing and observing Gemini chat models."""

from __future__ import annotations

from collections import defaultdict
from time import monotonic
from typing import Any, Literal, cast

import yaml
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from call_analyser.config import Settings
from call_analyser.errors import LLMBlockedError, StructuredOutputError

ModelRole = Literal["analysis", "fast", "transcribe"]


def get_chat_model(role: ModelRole, settings: Settings | None = None) -> Any:
    """Create a configured chat model without network access or eager invocation."""
    active = settings or Settings()
    model_by_role = {
        "analysis": active.analysis_model,
        "fast": active.fast_model,
        "transcribe": active.transcribe_model,
    }
    return init_chat_model(
        model=model_by_role[role],
        model_provider=active.chat_provider,
        temperature=0,
        max_retries=active.llm_max_retries,
        timeout=active.llm_timeout_s,
    )


def structured_model(model: Any, schema: type[BaseModel]) -> Any:
    """Apply the package's required provider structured-output boundary."""
    return model.with_structured_output(schema)


async def ainvoke_structured(
    model: Any, schema: type[BaseModel], input_value: Any, config: RunnableConfig
) -> BaseModel:
    """Invoke structured output and translate provider refusals into typed failures."""
    try:
        result = await structured_model(model, schema).ainvoke(input_value, config=config)
    except Exception as error:
        raise StructuredOutputError("structured model invocation failed") from error
    if isinstance(result, AIMessage):
        content = str(result.content)
        if "refusal" in content.lower() or "blocked" in content.lower():
            raise LLMBlockedError("model response was blocked or refused")
    if not isinstance(result, schema):
        raise StructuredOutputError("model did not return the requested schema")
    return result


class UsageTracker(AsyncCallbackHandler):
    """Accumulate per-stage latency and provider-reported token usage."""

    def __init__(self, pricing_path: str = "config/pricing.yaml") -> None:
        self.started: dict[Any, tuple[str, float]] = {}
        self.usage: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.prices = self._load_prices(pricing_path)

    @staticmethod
    def _load_prices(path: str) -> dict[str, dict[str, float]]:
        with open(path, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        return cast(dict[str, dict[str, float]], raw.get("models", {}))

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], *, run_id: Any, **kwargs: Any
    ) -> None:
        self.started[run_id] = (str(kwargs.get("tags", ["unknown"])[0]), monotonic())

    async def on_llm_end(self, response: Any, *, run_id: Any, **_: Any) -> None:
        stage, started_at = self.started.pop(run_id, ("unknown", monotonic()))
        bucket = self.usage[stage]
        bucket["latency_s"] += monotonic() - started_at
        message = response.generations[0][0].message if response.generations else None
        metadata = getattr(message, "usage_metadata", {}) if message is not None else {}
        call_usage: dict[str, float] = {}
        for source, target in (
            ("input_tokens", "input_tokens"),
            ("output_tokens", "output_tokens"),
            ("total_tokens", "total_tokens"),
        ):
            call_usage[target] = float((metadata or {}).get(source, 0))
            bucket[target] += call_usage[target]
        model = str(getattr(message, "response_metadata", {}).get("model_name", ""))
        prices = self.prices.get(model, {})
        bucket["cost"] += (
            call_usage["input_tokens"] * float(prices.get("input_per_million", 0))
            + call_usage["output_tokens"] * float(prices.get("output_per_million", 0))
        ) / 1_000_000
