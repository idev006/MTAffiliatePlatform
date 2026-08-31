from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferSelection,
)


class AffiliateOfferRepository(Protocol):
    def add_observations(self, observations: list[AffiliateOfferObservation]) -> int: ...

    def latest_for_product(
        self,
        product_id: str,
        affiliate_account_id: str | None = None,
    ) -> list[AffiliateOfferObservation]: ...

    def save_selection(self, selection: OfferSelection) -> None: ...

    def get_selection(self, selection_id: str) -> OfferSelection | None: ...
