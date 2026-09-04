from __future__ import annotations

from datetime import datetime
from typing import Protocol

from mtaffiliate.domain.worker_registry.models import WorkerHealthState, WorkerRecord


class WorkerRegistrationConflictError(ValueError):
    """Raised when a worker_id is already enrolled by a different installation."""


class UnknownWorkerError(ValueError):
    """Raised when a heartbeat targets a worker_id that was never registered."""


class WorkerRegistryRepository(Protocol):
    """Canonical Shared Core worker registry storage.

    Registry semantics:
    - register is idempotent for the same worker_id + installation_id (refreshes
      enrollment metadata and bumps version_no) and conflicts when the worker_id
      belongs to a different installation;
    - record_heartbeat fails closed with UnknownWorkerError for unregistered ids.
    """

    def register(self, record: WorkerRecord) -> WorkerRecord: ...

    def record_heartbeat(
        self,
        worker_id: str,
        *,
        health_state: WorkerHealthState,
        seen_at: datetime,
    ) -> WorkerRecord: ...

    def get(self, worker_id: str) -> WorkerRecord | None: ...

    def list(self) -> list[WorkerRecord]: ...
