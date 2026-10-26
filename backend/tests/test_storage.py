from pathlib import Path

import pytest

from analyser_api.storage.local import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_round_trip_and_ranges(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    source = tmp_path / "source.bin"
    source.write_bytes(b"0123456789")

    await storage.put("workspace/call/original.wav", source)

    assert await storage.size("workspace/call/original.wav") == 10
    assert await storage.open_range("workspace/call/original.wav", 2, 5) == b"2345"
    await storage.delete("workspace/call/original.wav")
    with pytest.raises(FileNotFoundError):
        await storage.size("workspace/call/original.wav")


@pytest.mark.asyncio
async def test_local_storage_rejects_path_escape(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    with pytest.raises(ValueError):
        await storage.size("../outside")
