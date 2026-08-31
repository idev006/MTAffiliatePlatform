from __future__ import annotations

import json
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferSelection,
)

from .models import AffiliateOfferObservationRow, AffiliateOfferSelectionRow


class SQLAlchemyAffiliateOfferRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _observation_to_domain(row: AffiliateOfferObservationRow) -> AffiliateOfferObservation:
        observed_at = row.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        return AffiliateOfferObservation(
            observation_id=row.observation_id,
            offer_id=row.offer_id,
            product_id=row.product_id,
            platform=row.platform,
            shop_id=row.shop_id,
            item_id=row.item_id,
            affiliate_account_id=row.affiliate_account_id,
            observed_at=observed_at,
            seller_name=row.seller_name,
            product_name=row.product_name,
            price_current=row.price_current,
            commission_rate=row.commission_rate,
            extra_commission_rate=row.extra_commission_rate,
            rating=row.rating,
            review_count=row.review_count,
            sold_signal=row.sold_signal,
            available=row.available,
        )

    @staticmethod
    def _selection_to_domain(row: AffiliateOfferSelectionRow) -> OfferSelection:
        selected_at = row.selected_at
        if selected_at.tzinfo is None:
            selected_at = selected_at.replace(tzinfo=UTC)
        return OfferSelection(
            selection_id=row.selection_id,
            product_id=row.product_id,
            preferred_offer_id=row.preferred_offer_id,
            backup_offer_ids=json.loads(row.backup_offer_ids),
            affiliate_account_id=row.affiliate_account_id,
            selected_at=selected_at,
            model_version=row.model_version,
        )

    def add_observations(self, observations: list[AffiliateOfferObservation]) -> int:
        accepted = 0
        with self._session_factory() as session, session.begin():
            for item in observations:
                existing = session.get(AffiliateOfferObservationRow, item.observation_id)
                if existing is not None:
                    if self._observation_to_domain(existing) != item:
                        raise ValueError("observation_id collision with different payload")
                    continue
                session.add(
                    AffiliateOfferObservationRow(
                        observation_id=item.observation_id,
                        offer_id=item.offer_id,
                        product_id=item.product_id,
                        platform=item.platform,
                        shop_id=item.shop_id,
                        item_id=item.item_id,
                        affiliate_account_id=item.affiliate_account_id,
                        observed_at=item.observed_at,
                        seller_name=item.seller_name,
                        product_name=item.product_name,
                        price_current=item.price_current,
                        commission_rate=item.commission_rate,
                        extra_commission_rate=item.extra_commission_rate,
                        rating=item.rating,
                        review_count=item.review_count,
                        sold_signal=item.sold_signal,
                        available=item.available,
                    )
                )
                accepted += 1
        return accepted

    def latest_for_product(
        self,
        product_id: str,
        affiliate_account_id: str | None = None,
    ) -> list[AffiliateOfferObservation]:
        query = select(AffiliateOfferObservationRow).where(
            AffiliateOfferObservationRow.product_id == product_id
        )
        if affiliate_account_id is not None:
            query = query.where(
                AffiliateOfferObservationRow.affiliate_account_id == affiliate_account_id
            )
        query = query.order_by(AffiliateOfferObservationRow.observed_at.desc())
        with self._session_factory() as session:
            rows = session.scalars(query).all()
        latest: dict[tuple[str, str, str, str, str], AffiliateOfferObservation] = {}
        for row in rows:
            item = self._observation_to_domain(row)
            latest.setdefault(item.commercial_key, item)
        return sorted(latest.values(), key=lambda item: item.commercial_key)

    def save_selection(self, selection: OfferSelection) -> None:
        with self._session_factory() as session, session.begin():
            existing = session.get(AffiliateOfferSelectionRow, selection.selection_id)
            if existing is not None:
                if self._selection_to_domain(existing) != selection:
                    raise ValueError("selection_id collision with different payload")
                return
            session.add(
                AffiliateOfferSelectionRow(
                    selection_id=selection.selection_id,
                    product_id=selection.product_id,
                    preferred_offer_id=selection.preferred_offer_id,
                    backup_offer_ids=json.dumps(selection.backup_offer_ids),
                    affiliate_account_id=selection.affiliate_account_id,
                    selected_at=selection.selected_at,
                    model_version=selection.model_version,
                )
            )

    def get_selection(self, selection_id: str) -> OfferSelection | None:
        with self._session_factory() as session:
            row = session.get(AffiliateOfferSelectionRow, selection_id)
            return None if row is None else self._selection_to_domain(row)
