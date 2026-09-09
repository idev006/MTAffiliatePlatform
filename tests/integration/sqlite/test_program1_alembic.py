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
    tables = set(inspect(engine).get_table_names())
    assert {
        "product_observations",
        "ingestion_batches",
        "workers",
        "jobs",
        "job_events",
        "program1_strategy_work",
        "program1_opportunity_decisions",
        "program2_work",
        "program2_selection_decisions",
        "program2_link_artifacts",
        "program3_devices",
        "program3_plans",
        "program3_pre_submit_decisions",
        "program3_submissions",
        "program3_reconciliations",
        "alembic_version",
    } <= tables
    engine.dispose()

    command.downgrade(config, "base")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert "product_observations" not in tables
    assert "ingestion_batches" not in tables
    assert "workers" not in tables
    assert "jobs" not in tables
    assert "job_events" not in tables
    assert "program1_strategy_work" not in tables
    assert "program1_opportunity_decisions" not in tables
    assert "program2_work" not in tables
    assert "program2_selection_decisions" not in tables
    assert "program2_link_artifacts" not in tables
    assert "program3_devices" not in tables
    assert "program3_plans" not in tables
    assert "program3_pre_submit_decisions" not in tables
    assert "program3_submissions" not in tables
    assert "program3_reconciliations" not in tables
    engine.dispose()


def test_repeated_upgrade_is_idempotent(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    database = tmp_path / "repeat.db"
    config = alembic_config(root, f"sqlite:///{database.as_posix()}")
    command.upgrade(config, "head")
    command.upgrade(config, "head")


def test_image_upgrade_preserves_existing_observations_and_receipts(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    url = f"sqlite:///{(tmp_path / 'legacy-image.db').as_posix()}"
    config = alembic_config(root, url)
    command.upgrade(config, "0011_program3_devices")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO product_observations (observation_id, platform, shop_id, item_id, collected_at, product_name) VALUES ('old', 'shopee', 's', 'i', '2026-09-09 00:00:00', 'Legacy')"
        )
        connection.exec_driver_sql(
            "INSERT INTO ingestion_batches (batch_id, fingerprint, accepted_count, received_count) VALUES ('old-batch', 'legacy-hash', 1, 1)"
        )
    engine.dispose()
    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT observation_id, primary_image_url FROM product_observations"
        ).all() == [("old", None)]
        assert connection.exec_driver_sql(
            "SELECT fingerprint, accepted_count, received_count FROM ingestion_batches"
        ).all() == [("legacy-hash", 1, 1)]
    engine.dispose()
