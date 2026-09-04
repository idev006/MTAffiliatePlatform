from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.program1.opportunity import OpportunityDecisionRecord


class OpportunityDecisionConflictError(RuntimeError):
    pass


class Program1OpportunityRepository(Protocol):
    def put(self, decision: OpportunityDecisionRecord) -> None: ...

    def get(self, decision_id: str) -> OpportunityDecisionRecord | None: ...

    def latest_for_product(
        self,
        product_key: tuple[str, str, str],
    ) -> OpportunityDecisionRecord | None: ...

    def list_for_campaign(self, campaign_id: str) -> list[OpportunityDecisionRecord]: ...
