from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferScore,
    OfferSelection,
)
from mtaffiliate.engines.affiliate_offer_engine.service import AffiliateOfferEngine
from mtaffiliate.ports.repositories.affiliate_offer import AffiliateOfferRepository


class Program2Service:
    def __init__(
        self,
        repository: AffiliateOfferRepository,
        engine: AffiliateOfferEngine,
    ) -> None:
        self.repository = repository
        self.engine = engine

    def ingest_observations(self, observations: list[AffiliateOfferObservation]) -> int:
        return self.repository.add_observations(observations)

    def rank_offers(
        self,
        product_id: str,
        *,
        affiliate_account_id: str | None = None,
    ) -> list[OfferScore]:
        observations = self.repository.latest_for_product(
            product_id,
            affiliate_account_id,
        )
        return self.engine.rank(observations)

    def select_offers(
        self,
        product_id: str,
        *,
        affiliate_account_id: str,
        backup_count: int = 2,
        now: datetime | None = None,
    ) -> OfferSelection:
        if backup_count < 0:
            raise ValueError("backup_count must be >= 0")
        ranked = self.rank_offers(
            product_id,
            affiliate_account_id=affiliate_account_id,
        )
        if not ranked:
            raise ValueError("no eligible affiliate offers")
        preferred = ranked[0]
        backups = ranked[1 : backup_count + 1]
        selection = OfferSelection(
            selection_id=f"sel-{uuid4().hex}",
            product_id=product_id,
            preferred_offer_id=preferred.commercial_key[3],
            backup_offer_ids=[item.commercial_key[3] for item in backups],
            affiliate_account_id=affiliate_account_id,
            selected_at=now or datetime.now(UTC),
            model_version=preferred.model_version,
        )
        self.repository.save_selection(selection)
        return selection
