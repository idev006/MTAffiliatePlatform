from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.ports.repositories.product import ObservationConflictError

from .models import ProductObservationRow


class SQLAlchemyProductRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: ProductObservationRow) -> ProductObservation:
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
    def _same(existing: ProductObservationRow, incoming: ProductObservation) -> bool:
        return SQLAlchemyProductRepository._to_domain(existing) == incoming

    @staticmethod
    def _row(observation: ProductObservation) -> ProductObservationRow:
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

    def add_observations(self, observations: list[ProductObservation]) -> int:
        accepted = 0
        with self._session_factory() as session, session.begin():
            for observation in observations:
                existing = session.scalar(
                    select(ProductObservationRow).where(
                        ProductObservationRow.observation_id == observation.observation_id
                    )
                )
                if existing is not None:
                    if not self._same(existing, observation):
                        raise ObservationConflictError(observation.observation_id)
                    continue

                try:
                    with session.begin_nested():
                        session.add(self._row(observation))
                        session.flush()
                except IntegrityError:
                    existing = session.scalar(
                        select(ProductObservationRow).where(
                            ProductObservationRow.observation_id == observation.observation_id
                        )
                    )
                    if existing is None or not self._same(existing, observation):
                        raise ObservationConflictError(observation.observation_id) from None
                    continue
                accepted += 1
        return accepted

    def latest_observations(self) -> list[ProductObservation]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(ProductObservationRow).order_by(
                    ProductObservationRow.platform,
                    ProductObservationRow.shop_id,
                    ProductObservationRow.item_id,
                    ProductObservationRow.collected_at.desc(),
                    ProductObservationRow.observation_id.desc(),
                )
            ).all()
        latest: dict[tuple[str, str, str], ProductObservation] = {}
        for row in rows:
            item = self._to_domain(row)
            latest.setdefault(item.canonical_key, item)
        return list(latest.values())
