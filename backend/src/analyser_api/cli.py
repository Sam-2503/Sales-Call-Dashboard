"""Administrative backend commands."""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
from contextlib import suppress
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import async_sessionmaker

from analyser_api.config import Settings
from analyser_api.db.engine import create_engine
from analyser_api.jobs.runner import PackageRunner
from analyser_api.jobs.worker import JobWorker
from analyser_api.openapi import OPENAPI_PATH, render_openapi
from analyser_api.services.demo import seed_demo_workspace
from analyser_api.services.playbook_artifact import publish, sync
from analyser_api.storage.factory import create_storage


def migrate() -> None:
    settings = Settings()
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url_direct or settings.database_url)
    command.upgrade(config, "head")


def export_openapi(*, check: bool) -> int:
    rendered = render_openapi()
    if check:
        if not OPENAPI_PATH.exists() or OPENAPI_PATH.read_text(encoding="utf-8") != rendered:
            print(f"OpenAPI drift detected: run 'make openapi' to refresh {OPENAPI_PATH.name}.")
            return 1
        return 0
    OPENAPI_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OPENAPI_PATH}")
    return 0


async def run_worker() -> None:
    settings = Settings()
    engine = create_engine(settings)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    storage = create_storage(settings)
    worker = JobWorker(
        session_factory,
        PackageRunner(settings, session_factory),
        storage,
        settings,
        worker_id=f"worker-{os.getpid()}",
    )
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(signum, stop_event.set)

    await worker.start()
    try:
        await stop_event.wait()
    finally:
        await worker.stop()
        await engine.dispose()


async def run_seed_demo(calls: int) -> None:
    settings = Settings()
    engine = create_engine(settings)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        workspace_id, token = await seed_demo_workspace(
            session_factory,
            settings,
            calls=calls,
            label="demo-seed",
            reuse=True,
        )
    finally:
        await engine.dispose()
    print(f"workspace_id={workspace_id}")
    print(f"token={token}")


def serve() -> None:
    settings = Settings()
    uvicorn.run(
        "analyser_api.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="analyser-api")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate", help="Apply database migrations.")
    openapi = subparsers.add_parser(
        "export-openapi", help="Write the deterministic OpenAPI schema."
    )
    openapi.add_argument(
        "--check", action="store_true", help="Fail when the committed schema drifts."
    )
    subparsers.add_parser("worker", help="Run the durable analysis worker.")
    subparsers.add_parser("serve", help="Run the HTTP service.")
    seed = subparsers.add_parser("seed-demo", help="Create or reuse deterministic demo data.")
    seed.add_argument("--calls", type=int, default=8)
    playbook = subparsers.add_parser("playbook", help="Publish or sync the playbook artifact.")
    playbook_sub = playbook.add_subparsers(dest="playbook_command", required=True)
    playbook_sub.add_parser("publish")
    playbook_sub.add_parser("sync")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "migrate":
        migrate()
    elif args.command == "export-openapi":
        raise SystemExit(export_openapi(check=bool(args.check)))
    elif args.command == "worker":
        asyncio.run(run_worker())
    elif args.command == "serve":
        serve()
    elif args.command == "seed-demo":
        asyncio.run(run_seed_demo(args.calls))
    elif args.command == "playbook":
        settings = Settings()
        if args.playbook_command == "publish":
            print(publish(settings))
        else:
            print("updated" if sync(settings) else "up-to-date")
    else:  # pragma: no cover - argparse enforces the choices
        raise SystemExit("unknown command")


if __name__ == "__main__":
    main()
