from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
    Program3OfferHandoff,
)
from mtaffiliate.ports.repositories.program2_artifact import Program2ArtifactRepository
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionRepository


@dataclass(frozen=True)
class Program2HandoffPolicy:
    version: str = "program2-program3-handoff-lab-v1"
    max_selection_age: timedelta = timedelta(hours=6)
    allowed_validation_states: tuple[LinkArtifactValidationState, ...] = (
        LinkArtifactValidationState.LAB_VALIDATED,
        LinkArtifactValidationState.EVIDENCE_VALIDATED,
    )

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("handoff policy version must be non-empty")
        if self.max_selection_age <= timedelta(0):
            raise ValueError("max_selection_age must be positive")
        if not self.allowed_validation_states:
            raise ValueError("allowed_validation_states must not be empty")


class Program2ArtifactService:
    def __init__(
        self,
        *,
        decisions: Program2DecisionRepository,
        artifacts: Program2ArtifactRepository,
        policy: Program2HandoffPolicy | None = None,
    ) -> None:
        self.decisions = decisions
        self.artifacts = artifacts
        self.policy = policy or Program2HandoffPolicy()

    @staticmethod
    def _validate_web_url(value: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("affiliate link artifact must contain a valid web URL")

    def register_artifact(self, artifact: AffiliateLinkArtifact) -> AffiliateLinkArtifact:
        decision = self.decisions.get(artifact.selection_decision_id)
        if decision is None:
            raise ValueError("selection decision does not exist")
        if artifact.source_job_id != decision.source_job_id:
            raise ValueError("artifact source_job_id does not match selection decision")
        if artifact.affiliate_account_id != decision.affiliate_account_id:
            raise ValueError("artifact affiliate account does not match selection decision")
        if artifact.offer_id != decision.preferred_offer_id:
            raise ValueError("artifact offer_id does not match preferred selection")
        if artifact.validated_at is not None and artifact.validated_at < artifact.created_at:
            raise ValueError("validated_at cannot precede artifact creation")
        self._validate_web_url(artifact.link_url)
        self.artifacts.put(artifact)
        return artifact

    def build_program3_handoff(
        self,
        selection_decision_id: str,
        *,
        as_of: datetime,
    ) -> Program3OfferHandoff:
        decision = self.decisions.get(selection_decision_id)
        if decision is None:
            raise ValueError("selection decision does not exist")

        age = as_of - decision.selected_at
        if age < timedelta(0):
            raise ValueError("handoff as_of cannot precede selection")
        if age > self.policy.max_selection_age:
            raise ValueError("selection is stale and must be refreshed before Program 3")

        artifact = self.artifacts.latest_for_selection(selection_decision_id)
        if artifact is None:
            raise ValueError("validated affiliate link artifact is required")
        if artifact.validation_state not in self.policy.allowed_validation_states:
            raise ValueError(
                f"artifact validation state is not handoff-ready: {artifact.validation_state.value}"
            )
        if artifact.validated_at is None:
            raise ValueError("handoff-ready artifact requires validated_at")

        evidence_refs = tuple(
            sorted(set(decision.evidence_refs) | set(artifact.evidence_refs))
        )
        return Program3OfferHandoff(
            handoff_id=f"p2h-{decision.decision_id}-{artifact.artifact_id}",
            selection_decision_id=decision.decision_id,
            affiliate_account_id=decision.affiliate_account_id,
            product_id=decision.product_id,
            preferred_offer_id=decision.preferred_offer_id,
            backup_offer_ids=decision.backup_offer_ids,
            link_artifact_id=artifact.artifact_id,
            valid_at=as_of,
            evidence_refs=evidence_refs,
        )
