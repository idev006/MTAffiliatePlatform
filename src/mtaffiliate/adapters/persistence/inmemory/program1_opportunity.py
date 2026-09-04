from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.program1.opportunity import OpportunityDecisionRecord
from mtaffiliate.ports.repositories.program1_opportunity import (
    OpportunityDecisionConflictError,
)


class InMemoryProgram1OpportunityRepository:
    def __init__(self) -> None:
        self._items: dict[str, OpportunityDecisionRecord] = {}
        self._lock = RLock()

    def put(self, decision: OpportunityDecisionRecord) -> None:
        with self._lock:
            existing = self._items.get(decision.decision_id)
            if existing is not None:
                if existing != decision:
                    raise OpportunityDecisionConflictError(
                        f"opportunity decision conflict: {decision.decision_id}"
                    )
                return
            self._items[decision.decision_id] = decision

    def get(self, decision_id: str) -> OpportunityDecisionRecord | None:
        with self._lock:
            return self._items.get(decision_id)

    def latest_for_product(
        self,
        product_key: tuple[str, str, str],
    ) -> OpportunityDecisionRecord | None:
        with self._lock:
            candidates = [
                decision
                for decision in self._items.values()
                if decision.thesis.product_key == product_key
            ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (item.evaluated_at, item.decision_id),
        )

    def list_for_campaign(self, campaign_id: str) -> list[OpportunityDecisionRecord]:
        with self._lock:
            items = [
                decision
                for decision in self._items.values()
                if decision.campaign_id == campaign_id
            ]
        return sorted(
            items,
            key=lambda item: (
                item.evaluated_at,
                item.decision_id,
            ),
            reverse=True,
        )
