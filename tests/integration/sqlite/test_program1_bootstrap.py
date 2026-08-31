from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import inspect

from mtaffiliate.adapters.persistence.sqlalchemy.factory import build_engine
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.bootstrap.migrations import upgrade_database_to_head
from mtaffiliate.bootstrap.program1 import build_durable_program1
from mtaffiliate.domain.product.models import ProductObservation

pytestmark = pytest.mark.integration


def observation() -> ProductObservation:
    return ProductObservation(
        observation_id="bootstrap-obs-1",
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        collected_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name="Bootstrap Product",
        price_current=Decimal(100),
        sold_signal=100,
        rating=4.5,
        review_count=20,
    )


def test_upgrade_database_to_head_creates_portable_schema(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    database = tmp_path / "portable-migrated.db"
    url = f"sqlite:///{database.as_posix()}"

    upgrade_database_to_head(url, project_root=root)

    engine = build_engine(url, project_root=root)
    tables = set(inspect(engine).get_table_names())
    assert {"product_observations", "ingestion_batches", "alembic_version"} <= tables
    engine.dispose()


def test_durable_program1_composition_survives_recomposition(tmp_path) -> None:
    root = Path(__file__).resolve().parents[3]
    database = tmp_path / "composition.db"
    url = f"sqlite:///{database.as_posix()}"
    settings = Settings(
        database={"url": url, "auto_migrate": False},
        program1={"shortlist_limit": 5, "minimum_score": 0},
    )
    upgrade_database_to_head(url, project_root=root)

    service = build_durable_program1(settings, project_root=root)
    first = service.ingest_batch("batch-bootstrap", [observation()])
    assert first.accepted_count == 1
    assert len(service.build_shortlist()) == 1

    restarted = build_durable_program1(settings, project_root=root)
    retry = restarted.ingest_batch("batch-bootstrap", [observation()])
    assert retry == first
    assert len(restarted.build_shortlist()) == 1
