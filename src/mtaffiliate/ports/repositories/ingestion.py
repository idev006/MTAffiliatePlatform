from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mtaffiliate.domain.product.models import ProductObservation


class IngestionBatchConflictError(ValueError):
    """Raised when a batch_id is reused with a different payload."""


@dataclass(frozen=True)
class IngestionBatchReceipt:
    fingerprint: str
    accepted_count: int
    received_count: int


class IngestionBatchIngestor(Protocol):
    """Atomically persist one logical batch and its durable receipt."""

    def ingest_batch(
        self,
        batch_id: str,
        fingerprint: str,
        observations: list[ProductObservation],
    ) -> IngestionBatchReceipt: ...
