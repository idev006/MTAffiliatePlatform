from __future__ import annotations

from mtaffiliate.domain.publishing.events import (
    ReconciliationDecision,
    ReconciliationEvidence,
)


class PublishReconciliationEngine:
    """Resolve unknown publish outcomes only from explicit evidence."""

    def reconcile(self, evidence: ReconciliationEvidence) -> ReconciliationDecision:
        if evidence.externally_confirmed and evidence.externally_absent:
            return ReconciliationDecision(
                resolved_status="NEEDS_HUMAN",
                reason="CONFLICTING_EXTERNAL_EVIDENCE",
            )
        if evidence.externally_confirmed:
            return ReconciliationDecision(
                resolved_status="CONFIRMED",
                reason="EXTERNAL_PUBLISH_EVIDENCE_CONFIRMED",
            )
        if evidence.externally_absent:
            return ReconciliationDecision(
                resolved_status="NOT_PUBLISHED",
                reason="EXTERNAL_EVIDENCE_CONFIRMS_ABSENCE",
            )
        return ReconciliationDecision(
            resolved_status="NEEDS_HUMAN",
            reason="INSUFFICIENT_EVIDENCE_TO_RESOLVE_OUTCOME",
        )
