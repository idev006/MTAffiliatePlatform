from __future__ import annotations

from threading import RLock

from mtaffiliate.ports.repositories.ingestion import (
    IngestionBatchConflictError,
    IngestionBatchReceipt,
)


class InMemoryIngestionBatchStore:
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
