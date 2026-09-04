from __future__ import annotations

from datetime import datetime
from threading import RLock

from mtaffiliate.domain.worker_registry.models import (
    WORKER_REPORTABLE_HEALTH_STATES,
    WorkerHealthState,
    WorkerRecord,
)
from mtaffiliate.ports.repositories.worker_registry import (
    UnknownWorkerError,
    WorkerRegistrationConflictError,
)


def _refresh_health_state(existing: WorkerRecord) -> WorkerHealthState:
    """Registration refreshes liveness but must not resurrect a Back Office disable."""
    if existing.health_state not in WORKER_REPORTABLE_HEALTH_STATES:
        return existing.health_state
    return WorkerHealthState.ONLINE_IDLE


class InMemoryWorkerRegistryRepository:
    def __init__(self) -> None:
        self._records: dict[str, WorkerRecord] = {}
        self._lock = RLock()

    def register(self, record: WorkerRecord) -> WorkerRecord:
        with self._lock:
            existing = self._records.get(record.worker_id)
            if existing is None:
                self._records[record.worker_id] = record
                return record
            if existing.installation_id != record.installation_id:
                raise WorkerRegistrationConflictError(
                    f"worker_id collision: {record.worker_id}"
                )
            refreshed = existing.model_copy(
                update={
                    "host_id": record.host_id,
                    "version": record.version,
                    "capabilities": record.capabilities,
                    "health_state": _refresh_health_state(existing),
                    "last_seen_at": record.last_seen_at,
                    "version_no": existing.version_no + 1,
                }
            )
            self._records[record.worker_id] = refreshed
            return refreshed

    def record_heartbeat(
        self,
        worker_id: str,
        *,
        health_state: WorkerHealthState,
        seen_at: datetime,
    ) -> WorkerRecord:
        with self._lock:
            existing = self._records.get(worker_id)
            if existing is None:
                raise UnknownWorkerError(f"unknown worker: {worker_id}")
            refreshed = existing.model_copy(
                update={
                    "health_state": health_state,
                    "last_seen_at": seen_at,
                    "version_no": existing.version_no + 1,
                }
            )
            self._records[worker_id] = refreshed
            return refreshed

    def get(self, worker_id: str) -> WorkerRecord | None:
        with self._lock:
            return self._records.get(worker_id)

    def list(self) -> list[WorkerRecord]:
        with self._lock:
            return list(self._records.values())
