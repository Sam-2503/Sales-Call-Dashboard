import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableConfig, chain
from pydantic import BaseModel

from events import ProgressCallbackHandler
from llm import UsageTracker
from persist import InMemoryStageStore, persisted
from prompts.registry import PromptError, PromptRegistry


def test_prompt_rendering_is_strict(tmp_path: Path) -> None:
    path = tmp_path / "demo"
    path.mkdir()
    (path / "v1.md").write_text(
        "---\nname: demo\nversion: v1\ninput_variables: [name]\n---\nHello {name}.\n"
    )
    prompt = PromptRegistry(tmp_path).load("demo")
    assert prompt.render(name="Ada") == "Hello Ada.\n"
    assert prompt.prompt_id.startswith("demo@v1+")
    with pytest.raises(PromptError):
        prompt.render(extra="x")


class Input(BaseModel):
    value: int


class Output(BaseModel):
    value: int


async def test_persisted_hit_miss_and_force_refresh() -> None:
    calls = 0

    @chain
    @persisted("toy")
    async def toy(input_value: Input, config: RunnableConfig) -> Output:
        nonlocal calls
        calls += 1
        return Output(value=input_value.value + calls)

    store = InMemoryStageStore()
    config: RunnableConfig = {"configurable": {"stage_store": store}}
    assert (await toy.ainvoke(Input(value=1), config)).value == 2
    assert (await toy.ainvoke(Input(value=1), config)).value == 2
    assert (
        await toy.ainvoke(
            Input(value=1), {"configurable": {"stage_store": store, "force_refresh": True}}
        )
    ).value == 3
    assert calls == 2


async def test_progress_events_arrive_in_order() -> None:
    events = []

    async def sink(event: object) -> None:
        events.append(event)

    handler = ProgressCallbackHandler(sink, {"toy"})

    @chain
    async def toy(value: int, config: RunnableConfig) -> int:
        return value + 1

    await toy.ainvoke(1, {"callbacks": [handler], "run_name": "toy"})
    assert [event.status for event in events] == ["started", "finished"]


async def test_usage_tracker_sums_fake_llm_usage(tmp_path: Path) -> None:
    price = tmp_path / "pricing.yaml"
    price.write_text("models: {}\n")
    tracker = UsageTracker(str(price))
    await tracker.on_llm_start({}, ["prompt"], run_id="r", tags=["rubric_results"])
    message = SimpleNamespace(
        usage_metadata={"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}
    )
    response = SimpleNamespace(generations=[[SimpleNamespace(message=message)]])
    await asyncio.sleep(0)
    await tracker.on_llm_end(response, run_id="r")
    assert tracker.usage["rubric_results"]["total_tokens"] == 7
