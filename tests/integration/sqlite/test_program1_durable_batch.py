from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import build_engine, build_session_factory
from mtaffiliate.adapters.persistence.sqlalchemy.ingestion import SQLAlchemyProgram1BatchIngestor
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)

pytestmark = pytest.mark.integration


def observation(item_id: str = "item-1") -> ProductObservation:
    return ProductObservation(
        observation_id="obs-1",
        platform="shopee",
        shop_id="shop-1",
        item_id=item_id,
        collected_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name=f"Product {item_id}",
        price_current=Decimal(100),
        sold_signal=100,
        rating=4.5,
        review_count=20,
    )


def service_for(tmp_path) -> tuple[Program1Service, object]:
    engine = build_engine("sqlite:///data/durable.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    service = Program1Service(
        SQLAlchemyProductRepository(sessions),
        ProductIntelligenceEngine(ScoringPolicy()),
        shortlist_limit=20,
        minimum_score=0,
        batch_ingestor=SQLAlchemyProgram1BatchIngestor(sessions),
    )
    return service, engine


def test_same_batch_retry_after_process_recomposition_returns_original_ack(tmp_path) -> None:
    first_service, engine = service_for(tmp_path)
    first = first_service.ingest_batch("batch-1", [observation()])
    assert first.accepted_count == 1
    engine.dispose()

    restarted_service, engine2 = service_for(tmp_path)
    retry = restarted_service.ingest_batch("batch-1", [observation()])
    assert retry == first
    assert len(restarted_service.repository.latest_observations()) == 1
    engine2.dispose()


def test_batch_id_collision_remains_conflict_after_restart(tmp_path) -> None:
    first_service, engine = service_for(tmp_path)
    first_service.ingest_batch("batch-1", [observation("item-A")])
    engine.dispose()

    restarted_service, engine2 = service_for(tmp_path)
    with pytest.raises(IngestionBatchConflictError):
        restarted_service.ingest_batch("batch-1", [observation("item-B")])
    engine2.dispose()
