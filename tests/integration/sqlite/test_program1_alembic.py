from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def alembic_config(root: Path, database_url: str) -> Config:
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_empty_sqlite_database_migrates_to_head_and_downgrades(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    database = tmp_path / "migration.db"
    url = f"sqlite:///{database.as_posix()}"
    config = alembic_config(root, url)

    command.upgrade(config, "head")
    engine = create_engine(url)
    inspector = inspect(engine)
    assert "product_observations" in inspector.get_table_names()
    assert "alembic_version" in inspector.get_table_names()
    engine.dispose()

    command.downgrade(config, "base")
    engine = create_engine(url)
    assert "product_observations" not in inspect(engine).get_table_names()
    engine.dispose()


def test_repeated_upgrade_is_idempotent(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    database = tmp_path / "repeat.db"
    config = alembic_config(root, f"sqlite:///{database.as_posix()}")
    command.upgrade(config, "head")
    command.upgrade(config, "head")
