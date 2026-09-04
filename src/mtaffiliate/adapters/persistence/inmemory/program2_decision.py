from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.affiliate_offer.models import OfferSelectionDecision
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionConflictError


class InMemoryProgram2DecisionRepository:
    def __init__(self) -> None:
        self._items: dict[str, OfferSelectionDecision] = {}
        self._lock = RLock()

    def put(self, decision: OfferSelectionDecision) -> None:
        with self._lock:
            existing = self._items.get(decision.decision_id)
            if existing is not None:
                if existing != decision:
                    raise Program2DecisionConflictError(
                        f"Program 2 decision conflict: {decision.decision_id}"
                    )
                return
            self._items[decision.decision_id] = decision

    def get(self, decision_id: str) -> OfferSelectionDecision | None:
        with self._lock:
            return self._items.get(decision_id)

    def latest_for_product_account(
        self,
        product_id: str,
        affiliate_account_id: str,
    ) -> OfferSelectionDecision | None:
        with self._lock:
            candidates = [
                decision
                for decision in self._items.values()
                if decision.product_id == product_id
                and decision.affiliate_account_id == affiliate_account_id
            ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: (item.selected_at, item.decision_id))
