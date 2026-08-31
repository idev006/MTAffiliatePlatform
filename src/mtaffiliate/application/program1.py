from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from threading import RLock

from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.engines.product_intelligence_engine.service import ProductIntelligenceEngine
from mtaffiliate.ports.repositories.product import ProductRepository


@dataclass(frozen=True)
class IngestResult:
    accepted_count: int
    received_count: int


class IngestionBatchConflictError(ValueError):
    """Raised when a batch_id is reused with a different payload."""


class Program1Service:
    def __init__(
        self,
        repository: ProductRepository,
        intelligence: ProductIntelligenceEngine,
        *,
        shortlist_limit: int,
        minimum_score: float,
    ) -> None:
        self.repository = repository
        self.intelligence = intelligence
        self.shortlist_limit = shortlist_limit
        self.minimum_score = minimum_score
        self._batches: dict[str, tuple[str, IngestResult]] = {}
        self._batch_lock = RLock()

    @staticmethod
    def _batch_fingerprint(observations: list[ProductObservation]) -> str:
        payload = [observation.model_dump(mode="json") for observation in observations]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def ingest(self, observations: list[ProductObservation]) -> IngestResult:
        accepted = self.repository.add_observations(observations)
        return IngestResult(accepted_count=accepted, received_count=len(observations))

    def ingest_batch(
        self,
        batch_id: str,
        observations: list[ProductObservation],
    ) -> IngestResult:
        if not batch_id.strip():
            raise ValueError("batch_id must be non-empty")
        fingerprint = self._batch_fingerprint(observations)
        with self._batch_lock:
            previous = self._batches.get(batch_id)
            if previous is not None:
                previous_fingerprint, previous_result = previous
                if previous_fingerprint != fingerprint:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
                return previous_result

            result = self.ingest(observations)
            self._batches[batch_id] = (fingerprint, result)
            return result

    def build_shortlist(self) -> list[ShortlistEntry]:
        latest = self.repository.latest_observations()
        return self.intelligence.shortlist(
            latest,
            limit=self.shortlist_limit,
            minimum_score=self.minimum_score,
        )
