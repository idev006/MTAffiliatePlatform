from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferSelection,
)


class InMemoryAffiliateOfferRepository:
    def __init__(self) -> None:
        self._observations: dict[str, AffiliateOfferObservation] = {}
        self._selections: dict[str, OfferSelection] = {}
        self._lock = RLock()

    def add_observations(self, observations: list[AffiliateOfferObservation]) -> int:
        accepted = 0
        with self._lock:
            for observation in observations:
                existing = self._observations.get(observation.observation_id)
                if existing is None:
                    self._observations[observation.observation_id] = observation
                    accepted += 1
                    continue
                if existing != observation:
                    raise ValueError("observation_id collision with different payload")
        return accepted

    def latest_for_product(
        self,
        product_id: str,
        affiliate_account_id: str | None = None,
    ) -> list[AffiliateOfferObservation]:
        with self._lock:
            matching = [
                item
                for item in self._observations.values()
                if item.product_id == product_id
                and (
                    affiliate_account_id is None
                    or item.affiliate_account_id == affiliate_account_id
                )
            ]
        latest: dict[tuple[str, str, str, str, str], AffiliateOfferObservation] = {}
        for item in matching:
            current = latest.get(item.commercial_key)
            if current is None or item.observed_at > current.observed_at:
                latest[item.commercial_key] = item
        return sorted(latest.values(), key=lambda item: item.commercial_key)

    def save_selection(self, selection: OfferSelection) -> None:
        with self._lock:
            existing = self._selections.get(selection.selection_id)
            if existing is not None and existing != selection:
                raise ValueError("selection_id collision with different payload")
            self._selections[selection.selection_id] = selection

    def get_selection(self, selection_id: str) -> OfferSelection | None:
        with self._lock:
            return self._selections.get(selection_id)
