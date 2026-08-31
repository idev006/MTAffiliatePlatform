from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IngestionBatchConflictError(ValueError):
    """Raised when a batch_id is reused with a different payload."""


@dataclass(frozen=True)
class IngestionBatchReceipt:
    fingerprint: str
    accepted_count: int
    received_count: int


class IngestionBatchStore(Protocol):
    def get(self, batch_id: str) -> IngestionBatchReceipt | None: ...

    def put(self, batch_id: str, receipt: IngestionBatchReceipt) -> None: ...
