from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from mtaffiliate.adapters.persistence.sqlalchemy.factory import resolve_database_url


def upgrade_database_to_head(database_url: str, *, project_root: Path) -> None:
    root = project_root.resolve()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", resolve_database_url(database_url, root))
    command.upgrade(config, "head")
