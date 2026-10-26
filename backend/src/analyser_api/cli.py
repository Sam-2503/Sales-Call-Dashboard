"""Administrative backend commands."""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from analyser_api.config import Settings


def migrate() -> None:
    settings = Settings()
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] != "migrate":
        raise SystemExit("usage: analyser-api migrate")
    migrate()


if __name__ == "__main__":
    main()
