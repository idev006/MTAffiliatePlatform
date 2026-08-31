from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.adapters.persistence.inmemory.product import ObservationConflictError
from mtaffiliate.domain.product.models import ProductObservation

from .models import ProductObservationRow


class SQLAlchemyProductRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: ProductObservationRow) -> ProductObservation:
        return ProductObservation(
            observation_id=row.observation_id,
            platform=row.platform,
            shop_id=row.shop_id,
            item_id=row.item_id,
            collected_at=row.collected_at,
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

    def add_observations(self, observations: list[ProductObservation]) -> int:
        accepted = 0
        with self._session_factory() as session:
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
                session.add(
                    ProductObservationRow(
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
                )
                try:
                    session.flush()
                except IntegrityError as exc:
                    session.rollback()
                    raise ObservationConflictError(observation.observation_id) from exc
                accepted += 1
            session.commit()
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
