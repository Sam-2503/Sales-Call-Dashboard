from __future__ import annotations

import asyncio
import getpass
import os
import shutil
import socket
import subprocess
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from analyser_api.db.models import Base


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    configured = os.getenv("TEST_DATABASE_URL")
    if configured:
        yield configured
        return
    initdb = shutil.which("initdb")
    pg_ctl = shutil.which("pg_ctl")
    if initdb and pg_ctl:
        directory = tempfile.mkdtemp(prefix="analyser-pg-")
        data = Path(directory) / "data"
        port = _free_port()
        user = getpass.getuser()
        try:
            subprocess.run(
                [initdb, "-D", str(data), "--auth=trust", "-U", user],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            subprocess.run(
                [
                    pg_ctl,
                    "-D",
                    str(data),
                    "-o",
                    f"-p {port} -h 127.0.0.1",
                    "-w",
                    "start",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            yield f"postgresql+asyncpg://{user}@127.0.0.1:{port}/postgres"
        finally:
            subprocess.run(
                [pg_ctl, "-D", str(data), "-m", "immediate", "stop"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                check=False,
            )
            shutil.rmtree(directory, ignore_errors=True)
        return
    try:
        import fasteners
        from pgserver import PostgresServer, get_server
    except ImportError:
        pytest.skip(
            "PostgreSQL is unavailable: set TEST_DATABASE_URL, install initdb/pg_ctl, "
            "or run the test extra on Python 3.12 with pgserver. Database tests were not run."
        )
    runtime = Path(tempfile.mkdtemp(prefix="analyser-pgserver-runtime-"))
    PostgresServer.runtime_path = runtime
    PostgresServer.lock_path = runtime / ".lockfile"
    PostgresServer._lock = fasteners.InterProcessLock(PostgresServer.lock_path)
    directory = tempfile.mkdtemp(prefix="analyser-pgserver-")
    server = get_server(Path(directory) / "data", cleanup_mode="delete")
    try:
        yield server.get_uri().replace("postgresql://", "postgresql+asyncpg://", 1)
    finally:
        server.cleanup()
        shutil.rmtree(directory, ignore_errors=True)
        shutil.rmtree(runtime, ignore_errors=True)


@pytest.fixture
async def db_engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture
async def db_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_session_factory() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    return asyncio.get_event_loop_policy()
