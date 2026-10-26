"""Filesystem audio storage for development and single-instance deployments."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class LocalStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("invalid storage key")
        return path

    async def put(self, key: str, path: Path) -> None:
        destination = self._path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copyfile, path, destination)

    async def open_range(self, key: str, start: int, end: int) -> bytes:
        def read() -> bytes:
            with self._path(key).open("rb") as stream:
                stream.seek(start)
                return stream.read(end - start + 1)

        return await asyncio.to_thread(read)

    async def size(self, key: str) -> int:
        return (await asyncio.to_thread(self._path(key).stat)).st_size

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, missing_ok=True)

    async def delete_prefix(self, prefix: str) -> None:
        path = self._path(prefix)
        if path.exists():
            await asyncio.to_thread(shutil.rmtree, path)

    async def healthcheck(self) -> None:
        await asyncio.to_thread(self.root.mkdir, parents=True, exist_ok=True)
