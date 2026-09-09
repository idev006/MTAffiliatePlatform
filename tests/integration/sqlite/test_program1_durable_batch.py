from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import build_engine, build_session_factory
from mtaffiliate.adapters.persistence.sqlalchemy.ingestion import SQLAlchemyProgram1BatchIngestor
from mtaffiliate.adapters.persistence.sqlalchemy.models import (
    IngestionBatchRow,
    ProductObservationRow,
)
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)
from mtaffiliate.ports.repositories.product import ObservationConflictError

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


def test_batch_preserves_job_provenance_and_duplicate_receipt_after_restart(tmp_path) -> None:
    service, engine = service_for(tmp_path)
    original = observation().model_copy(
        update={"source_job_id": "job-1", "source_worker_id": "worker-1"}
    )
    service.ingest_batch("original", [original])
    assert service.repository.observation_history(original.canonical_key) == [original]
    engine.dispose()

    restarted, engine2 = service_for(tmp_path)
    newer = original.model_copy(update={"observation_id": "obs-2"})
    mixed = restarted.ingest_batch("mixed", [original, newer, original])
    assert (mixed.accepted_count, mixed.duplicate_count, mixed.accounted_count) == (1, 2, 3)
    engine2.dispose()

    final, engine3 = service_for(tmp_path)
    assert final.ingest_batch("mixed", [original, newer, original]) == mixed
    duplicate = final.ingest_batch("duplicate-only", [original])
    assert (duplicate.accepted_count, duplicate.duplicate_count) == (0, 1)
    with pytest.raises(ObservationConflictError):
        final.ingest_batch(
            "conflicting-job", [original.model_copy(update={"source_job_id": "job-2"})]
        )
    with build_session_factory(engine3)() as session:
        assert session.scalar(select(func.count()).select_from(ProductObservationRow)) == 2
        assert session.scalar(select(func.count()).select_from(IngestionBatchRow)) == 3
        assert set(session.scalars(select(ProductObservationRow.source_job_id))) == {"job-1"}
    engine3.dispose()


def test_image_reference_survives_restart_and_conflicting_replay(tmp_path) -> None:
    service, engine = service_for(tmp_path)
    item = observation().model_copy(
        update={"primary_image_url": "https://example.test/product.jpg"}
    )
    receipt = service.ingest_batch("image-batch", [item])
    engine.dispose()
    service, engine = service_for(tmp_path)
    assert service.repository.latest_observations()[0].primary_image_url == item.primary_image_url
    assert service.ingest_batch("image-batch", [item]) == receipt
    assert service.ingest_batch("image-duplicate", [item]).duplicate_count == 1
    changed = item.model_copy(update={"primary_image_url": "https://example.test/changed.jpg"})
    with pytest.raises(IngestionBatchConflictError):
        service.ingest_batch("image-batch", [changed])
    with pytest.raises(ObservationConflictError):
        service.ingest_batch("image-conflict", [changed])
    assert service.repository.observation_history(item.canonical_key) == [item]
    engine.dispose()
