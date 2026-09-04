from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.affiliate_offer.models import AffiliateLinkArtifact
from mtaffiliate.ports.repositories.program2_artifact import Program2ArtifactConflictError


class InMemoryProgram2ArtifactRepository:
    def __init__(self) -> None:
        self._items: dict[str, AffiliateLinkArtifact] = {}
        self._lock = RLock()

    def put(self, artifact: AffiliateLinkArtifact) -> None:
        with self._lock:
            existing = self._items.get(artifact.artifact_id)
            if existing is not None:
                if existing != artifact:
                    raise Program2ArtifactConflictError(
                        f"Program 2 artifact conflict: {artifact.artifact_id}"
                    )
                return
            self._items[artifact.artifact_id] = artifact

    def get(self, artifact_id: str) -> AffiliateLinkArtifact | None:
        with self._lock:
            return self._items.get(artifact_id)

    def latest_for_selection(self, selection_decision_id: str) -> AffiliateLinkArtifact | None:
        with self._lock:
            candidates = [
                artifact
                for artifact in self._items.values()
                if artifact.selection_decision_id == selection_decision_id
            ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                item.validated_at or item.created_at,
                item.artifact_id,
            ),
        )
