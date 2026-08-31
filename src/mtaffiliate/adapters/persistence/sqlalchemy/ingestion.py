from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.ports.repositories.ingestion import (
    IngestionBatchConflictError,
    IngestionBatchReceipt,
)
from mtaffiliate.ports.repositories.product import ObservationConflictError

from .models import IngestionBatchRow, ProductObservationRow


class SQLAlchemyProgram1BatchIngestor:
    """Persist batch identity, observations and ACK receipt in one transaction."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _receipt(row: IngestionBatchRow) -> IngestionBatchReceipt:
        return IngestionBatchReceipt(
            fingerprint=row.fingerprint,
            accepted_count=row.accepted_count,
            received_count=row.received_count,
        )

    @staticmethod
    def _observation_from_row(row: ProductObservationRow) -> ProductObservation:
        collected_at = row.collected_at
        if collected_at.tzinfo is None:
            collected_at = collected_at.replace(tzinfo=UTC)
        return ProductObservation(
            observation_id=row.observation_id,
            platform=row.platform,
            shop_id=row.shop_id,
            item_id=row.item_id,
            collected_at=collected_at,
            product_name=row.product_name,
            product_url=row.product_url,
            price_current=row.price_current,
            sold_signal=row.sold_signal,
            rating=row.rating,
            review_count=row.review_count,
            source_worker_id=row.source_worker_id,
            source_query=row.source_query,
            extractor_version=row.extractor_version,
        )

    @staticmethod
    def _observation_row(observation: ProductObservation) -> ProductObservationRow:
        return ProductObservationRow(
            observation_id=observation.observation_id,
            platform=observation.platform,
            shop_id=observation.shop_id,
            item_id=observation.item_id,
            collected_at=observation.collected_at,
            product_name=observation.product_name,
            product_url=observation.product_url,
            price_current=observation.price_current,
            sold_signal=observation.sold_signal,
            rating=observation.rating,
            review_count=observation.review_count,
            source_worker_id=observation.source_worker_id,
            source_query=observation.source_query,
            extractor_version=observation.extractor_version,
        )

    def _ingest_once(
        self,
        batch_id: str,
        fingerprint: str,
        observations: list[ProductObservation],
    ) -> IngestionBatchReceipt:
        with self._session_factory() as session, session.begin():
            existing_batch = session.get(IngestionBatchRow, batch_id)
            if existing_batch is not None:
                receipt = self._receipt(existing_batch)
                if receipt.fingerprint != fingerprint:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
                return receipt

            batch_row = IngestionBatchRow(
                batch_id=batch_id,
                fingerprint=fingerprint,
                accepted_count=0,
                received_count=len(observations),
            )
            session.add(batch_row)
            session.flush()

            accepted = 0
            for observation in observations:
                existing = session.scalar(
                    select(ProductObservationRow).where(
                        ProductObservationRow.observation_id == observation.observation_id
                    )
                )
                if existing is not None:
                    if self._observation_from_row(existing) != observation:
                        raise ObservationConflictError(
                            f"observation_id collision: {observation.observation_id}"
                        )
                    continue

                session.add(self._observation_row(observation))
                session.flush()
                accepted += 1

            batch_row.accepted_count = accepted
            return IngestionBatchReceipt(
                fingerprint=fingerprint,
                accepted_count=accepted,
                received_count=len(observations),
            )

    def ingest_batch(
        self,
        batch_id: str,
        fingerprint: str,
        observations: list[ProductObservation],
    ) -> IngestionBatchReceipt:
        """Retry one whole transaction after a unique race.

        Retrying the complete transaction avoids exposing a partially finalized
        batch claim and keeps facts + ACK receipt in one atomic boundary.
        """
        try:
            return self._ingest_once(batch_id, fingerprint, observations)
        except IntegrityError:
            return self._ingest_once(batch_id, fingerprint, observations)
