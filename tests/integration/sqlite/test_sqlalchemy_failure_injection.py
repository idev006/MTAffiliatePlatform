from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from mtaffiliate.adapters.persistence.sqlalchemy.ingestion import SQLAlchemyProgram1BatchIngestor
from mtaffiliate.adapters.persistence.sqlalchemy.models import (
    IngestionBatchRow,
    ProductObservationRow,
)
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.ports.repositories.ingestion import IngestionBatchConflictError
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


def row_from(item: ProductObservation) -> ProductObservationRow:
    return ProductObservationRow(
        observation_id=item.observation_id,
        platform=item.platform,
        shop_id=item.shop_id,
        item_id=item.item_id,
        collected_at=item.collected_at,
        product_name=item.product_name,
        product_url=item.product_url,
        price_current=item.price_current,
        sold_signal=item.sold_signal,
        rating=item.rating,
        review_count=item.review_count,
        source_worker_id=item.source_worker_id,
        source_query=item.source_query,
        extractor_version=item.extractor_version,
    )


class FakeSession:
    def __init__(self, *, gets=None, scalar_values=None, flush_errors=None) -> None:
        self.gets = list(gets or [])
        self.scalar_values = list(scalar_values or [])
        self.flush_errors = list(flush_errors or [])
        self.added = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def begin(self):
        return nullcontext()

    def begin_nested(self):
        return nullcontext()

    def get(self, *_args):
        return self.gets.pop(0) if self.gets else None

    def scalar(self, *_args):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        if self.flush_errors:
            error = self.flush_errors.pop(0)
            if error is not None:
                raise error


class SequenceFactory:
    def __init__(self, *sessions: FakeSession) -> None:
        self.sessions = list(sessions)

    def __call__(self) -> FakeSession:
        return self.sessions.pop(0)


def integrity_error() -> IntegrityError:
    return IntegrityError("insert", {}, Exception("unique race"))


def test_batch_claim_unique_race_retries_and_returns_existing_receipt() -> None:
    existing = IngestionBatchRow(
        batch_id="batch-1",
        fingerprint="abc",
        accepted_count=3,
        received_count=3,
    )
    first = FakeSession(gets=[None], flush_errors=[integrity_error()])
    second = FakeSession(gets=[existing])
    ingestor = SQLAlchemyProgram1BatchIngestor(SequenceFactory(first, second))

    receipt = ingestor.ingest_batch("batch-1", "abc", [])

    assert receipt.accepted_count == 3
    assert receipt.received_count == 3


def test_batch_claim_unique_race_then_changed_payload_is_conflict() -> None:
    existing = IngestionBatchRow(
        batch_id="batch-1",
        fingerprint="other",
        accepted_count=1,
        received_count=1,
    )
    first = FakeSession(gets=[None], flush_errors=[integrity_error()])
    second = FakeSession(gets=[existing])
    ingestor = SQLAlchemyProgram1BatchIngestor(SequenceFactory(first, second))

    with pytest.raises(IngestionBatchConflictError):
        ingestor.ingest_batch("batch-1", "abc", [])


def test_observation_unique_race_retries_whole_batch_idempotently() -> None:
    item = observation()
    first = FakeSession(
        gets=[None],
        scalar_values=[None],
        flush_errors=[None, integrity_error()],
    )
    second = FakeSession(
        gets=[None],
        scalar_values=[row_from(item)],
        flush_errors=[None],
    )
    ingestor = SQLAlchemyProgram1BatchIngestor(SequenceFactory(first, second))

    receipt = ingestor.ingest_batch("batch-1", "abc", [item])

    assert receipt.accepted_count == 0
    assert receipt.received_count == 1


def test_observation_unique_race_retries_and_detects_collision() -> None:
    incoming = observation("item-A")
    first = FakeSession(
        gets=[None],
        scalar_values=[None],
        flush_errors=[None, integrity_error()],
    )
    second = FakeSession(
        gets=[None],
        scalar_values=[row_from(observation("item-B"))],
        flush_errors=[None],
    )
    ingestor = SQLAlchemyProgram1BatchIngestor(SequenceFactory(first, second))

    with pytest.raises(ObservationConflictError):
        ingestor.ingest_batch("batch-1", "abc", [incoming])


def test_product_repository_unique_race_is_idempotent_for_same_fact() -> None:
    item = observation()
    session = FakeSession(
        scalar_values=[None, row_from(item)],
        flush_errors=[integrity_error()],
    )
    repo = SQLAlchemyProductRepository(lambda: session)
    assert repo.add_observations([item]) == 0


def test_product_repository_unique_race_detects_collision() -> None:
    incoming = observation("item-A")
    session = FakeSession(
        scalar_values=[None, row_from(observation("item-B"))],
        flush_errors=[integrity_error()],
    )
    repo = SQLAlchemyProductRepository(lambda: session)
    with pytest.raises(ObservationConflictError):
        repo.add_observations([incoming])
