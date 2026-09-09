from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from threading import RLock

from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.engines.product_intelligence_engine.service import ProductIntelligenceEngine
from mtaffiliate.ports.repositories.ingestion import (
    IngestionBatchConflictError,
    IngestionBatchIngestor,
    IngestionBatchReceipt,
)
from mtaffiliate.ports.repositories.product import ProductRepository


@dataclass(frozen=True)
class IngestResult:
    accepted_count: int
    received_count: int

    @property
    def duplicate_count(self) -> int:
        """Exact entries already represented at the original atomic commit."""
        return self.received_count - self.accepted_count

    @property
    def accounted_count(self) -> int:
        return self.received_count


class _EphemeralBatchIngestor:
    """Atomic within one process; production composition injects a durable ingestor."""

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository
        self._items: dict[str, IngestionBatchReceipt] = {}
        self._lock = RLock()

    def ingest_batch(
        self,
        batch_id: str,
        fingerprint: str,
        observations: list[ProductObservation],
    ) -> IngestionBatchReceipt:
        with self._lock:
            existing = self._items.get(batch_id)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
                return existing

            accepted = self._repository.add_observations(observations)
            receipt = IngestionBatchReceipt(
                fingerprint=fingerprint,
                accepted_count=accepted,
                received_count=len(observations),
            )
            self._items[batch_id] = receipt
            return receipt


class Program1Service:
    def __init__(
        self,
        repository: ProductRepository,
        intelligence: ProductIntelligenceEngine,
        *,
        shortlist_limit: int,
        minimum_score: float,
        batch_ingestor: IngestionBatchIngestor | None = None,
    ) -> None:
        self.repository = repository
        self.intelligence = intelligence
        self.shortlist_limit = shortlist_limit
        self.minimum_score = minimum_score
        self.batch_ingestor = batch_ingestor or _EphemeralBatchIngestor(repository)

    @staticmethod
    def _batch_fingerprint(observations: list[ProductObservation]) -> str:
        payload = [observation.model_dump(mode="json") for observation in observations]
        for item in payload:
            if item["primary_image_url"] is None:
                del item["primary_image_url"]
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
        receipt = self.batch_ingestor.ingest_batch(
            batch_id,
            self._batch_fingerprint(observations),
            observations,
        )
        return IngestResult(
            accepted_count=receipt.accepted_count,
            received_count=receipt.received_count,
        )

    def build_shortlist(self) -> list[ShortlistEntry]:
        latest = self.repository.latest_observations()
        return self.intelligence.shortlist(
            latest,
            limit=self.shortlist_limit,
            minimum_score=self.minimum_score,
        )

    def observation_evidence(
        self, product_key: tuple[str, str, str], *, limit: int = 50
    ) -> list[ProductObservation]:
        if not 1 <= limit <= 100:
            raise ValueError("observation evidence limit must be between 1 and 100")
        history = self.repository.observation_history(product_key)
        return list(reversed(history[-limit:]))
