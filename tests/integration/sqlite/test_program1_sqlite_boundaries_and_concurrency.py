from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from threading import Barrier

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
    resolve_database_url,
)
from mtaffiliate.adapters.persistence.sqlalchemy.ingestion import SQLAlchemyProgram1BatchIngestor
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)

pytestmark = pytest.mark.integration


def observation(observation_id: str = "obs-1") -> ProductObservation:
    return ProductObservation(
        observation_id=observation_id,
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        collected_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name="Concurrent Product",
        price_current=Decimal(100),
        sold_signal=100,
        rating=4.5,
        review_count=20,
    )


def test_database_url_resolution_boundary_cases(tmp_path) -> None:
    assert resolve_database_url("sqlite:///:memory:", tmp_path) == "sqlite:///:memory:"
    postgres = "postgresql+psycopg://user:pass@db/app"
    assert resolve_database_url(postgres, tmp_path) == postgres

    absolute = f"sqlite:////{(tmp_path / 'absolute.db').as_posix().lstrip('/')}"
    assert resolve_database_url(absolute, tmp_path) == absolute


def test_symlink_escape_from_managed_sqlite_path_is_rejected(tmp_path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not available in this environment")

    with pytest.raises(ValueError, match="escapes project root"):
        resolve_database_url("sqlite:///escape/app.db", tmp_path)


def test_sqlite_pragmas_are_applied(tmp_path) -> None:
    engine = build_engine("sqlite:///data/pragmas.db", project_root=tmp_path)
    with engine.connect() as connection:
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        busy_timeout = connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
    assert foreign_keys == 1
    assert busy_timeout == 5000
    assert str(journal_mode).lower() == "wal"
    engine.dispose()


def test_concurrent_same_observation_is_logically_accepted_once(tmp_path) -> None:
    engine = build_engine("sqlite:///data/concurrent-observation.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    barrier = Barrier(2)

    def ingest() -> int:
        repo = SQLAlchemyProductRepository(sessions)
        barrier.wait()
        return repo.add_observations([observation()])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: ingest(), range(2)))

    assert sorted(results) == [0, 1]
    assert len(SQLAlchemyProductRepository(sessions).latest_observations()) == 1
    engine.dispose()


def test_concurrent_same_batch_returns_same_durable_receipt(tmp_path) -> None:
    engine = build_engine("sqlite:///data/concurrent-batch.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    barrier = Barrier(2)

    def ingest() -> tuple[int, int]:
        service = Program1Service(
            SQLAlchemyProductRepository(sessions),
            ProductIntelligenceEngine(ScoringPolicy()),
            shortlist_limit=20,
            minimum_score=0,
            batch_ingestor=SQLAlchemyProgram1BatchIngestor(sessions),
        )
        barrier.wait()
        result = service.ingest_batch("shared-batch", [observation()])
        return result.accepted_count, result.received_count

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: ingest(), range(2)))

    assert results == [(1, 1), (1, 1)]
    assert len(SQLAlchemyProductRepository(sessions).latest_observations()) == 1
    engine.dispose()
