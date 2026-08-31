from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from threading import RLock

from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.engines.product_intelligence_engine.service import ProductIntelligenceEngine
from mtaffiliate.ports.repositories.ingestion import (
    IngestionBatchConflictError,
    IngestionBatchReceipt,
    IngestionBatchStore,
)
from mtaffiliate.ports.repositories.product import ProductRepository


@dataclass(frozen=True)
class IngestResult:
    accepted_count: int
    received_count: int


class _EphemeralBatchStore:
    """Default test/development store. Production composition should inject durable storage."""

    def __init__(self) -> None:
        self._items: dict[str, IngestionBatchReceipt] = {}
        self._lock = RLock()

    def get(self, batch_id: str) -> IngestionBatchReceipt | None:
        with self._lock:
            return self._items.get(batch_id)

    def put(self, batch_id: str, receipt: IngestionBatchReceipt) -> None:
        with self._lock:
            existing = self._items.get(batch_id)
            if existing is not None and existing != receipt:
                raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
            self._items.setdefault(batch_id, receipt)


class Program1Service:
    def __init__(
        self,
        repository: ProductRepository,
        intelligence: ProductIntelligenceEngine,
        *,
        shortlist_limit: int,
        minimum_score: float,
        batch_store: IngestionBatchStore | None = None,
    ) -> None:
        self.repository = repository
        self.intelligence = intelligence
        self.shortlist_limit = shortlist_limit
        self.minimum_score = minimum_score
        self.batch_store = batch_store or _EphemeralBatchStore()
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
            previous = self.batch_store.get(batch_id)
            if previous is not None:
                if previous.fingerprint != fingerprint:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
                return IngestResult(
                    accepted_count=previous.accepted_count,
                    received_count=previous.received_count,
                )

            result = self.ingest(observations)
            self.batch_store.put(
                batch_id,
                IngestionBatchReceipt(
                    fingerprint=fingerprint,
                    accepted_count=result.accepted_count,
                    received_count=result.received_count,
                ),
            )
            return result

    def build_shortlist(self) -> list[ShortlistEntry]:
        latest = self.repository.latest_observations()
        return self.intelligence.shortlist(
            latest,
            limit=self.shortlist_limit,
            minimum_score=self.minimum_score,
        )
