from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.affiliate_offer.models import OfferSelectionDecision


class Program2DecisionConflictError(RuntimeError):
    pass


class Program2DecisionRepository(Protocol):
    def put(self, decision: OfferSelectionDecision) -> None: ...

    def get(self, decision_id: str) -> OfferSelectionDecision | None: ...

    def latest_for_product_account(
        self,
        product_id: str,
        affiliate_account_id: str,
    ) -> OfferSelectionDecision | None: ...
