from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.affiliate_offer.models import AffiliateLinkArtifact


class Program2ArtifactConflictError(RuntimeError):
    pass


class Program2ArtifactRepository(Protocol):
    def put(self, artifact: AffiliateLinkArtifact) -> None: ...

    def get(self, artifact_id: str) -> AffiliateLinkArtifact | None: ...

    def latest_for_selection(self, selection_decision_id: str) -> AffiliateLinkArtifact | None: ...
