"""Administrative backend commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

from analyser_api.config import Settings
from analyser_api.openapi import OPENAPI_PATH, render_openapi


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
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "migrate":
        migrate()
    elif args.command == "export-openapi":
        raise SystemExit(export_openapi(check=bool(args.check)))
    else:  # pragma: no cover - argparse enforces the choices
        raise SystemExit("unknown command")


if __name__ == "__main__":
    main()
