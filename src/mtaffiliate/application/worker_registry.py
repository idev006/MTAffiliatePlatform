from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mtaffiliate.domain.worker_registry.models import (
    WORKER_REPORTABLE_HEALTH_STATES,
    WorkerHealthState,
    WorkerRecord,
    WorkerRegistration,
    WorkerSummary,
)
from mtaffiliate.ports.repositories.worker_registry import WorkerRegistryRepository

# OFFLINE is derived when a worker has not been seen for this many heartbeat
# intervals; heartbeat_seconds remains the configuration-owned cadence knob.
DEFAULT_STALE_HEARTBEAT_MULTIPLIER = 3


class WorkerRegistryService:
    """Deterministic registry rules for Shared Core workers.

    The registry stores canonical enrollment state; Back Office owns transitions.
    OFFLINE is a derived operator view (staleness) rather than a writer-side sweep,
    so heartbeat loss is observable without a background mutation job.
    """

    def __init__(
        self,
        repository: WorkerRegistryRepository,
        *,
        stale_after: timedelta,
    ) -> None:
        if stale_after <= timedelta(0):
            raise ValueError("stale_after must be positive")
        self.repository = repository
        self.stale_after = stale_after

    def register(self, registration: WorkerRegistration, *, seen_at: datetime) -> WorkerRecord:
        record = WorkerRecord(
            worker_id=registration.worker_id,
            worker_type=registration.worker_type,
            installation_id=registration.installation_id,
            host_id=registration.host_id,
            version=registration.version,
            capabilities=registration.clean_capabilities,
            health_state=WorkerHealthState.ONLINE_IDLE,
            enrolled_at=seen_at,
            last_seen_at=seen_at,
            version_no=1,
        )
        return self.repository.register(record)

    def record_heartbeat(
        self,
        worker_id: str,
        *,
        health_state: WorkerHealthState,
        seen_at: datetime,
    ) -> WorkerRecord:
        if health_state not in WORKER_REPORTABLE_HEALTH_STATES:
            raise ValueError(
                "worker may only report ONLINE_IDLE, ONLINE_BUSY or DEGRADED; "
                f"received {health_state.value}"
            )
        return self.repository.record_heartbeat(
            worker_id,
            health_state=health_state,
            seen_at=seen_at,
        )

    def summary(self, worker_id: str, *, now: datetime) -> WorkerSummary | None:
        record = self.repository.get(worker_id)
        if record is None:
            return None
        return self._summarize(record, now=now)

    def summaries(self, *, now: datetime) -> list[WorkerSummary]:
        return [
            self._summarize(record, now=now)
            for record in sorted(self.repository.list(), key=lambda item: item.worker_id)
        ]

    def _summarize(self, record: WorkerRecord, *, now: datetime) -> WorkerSummary:
        stale = (
            record.health_state in WORKER_REPORTABLE_HEALTH_STATES
            and now - record.last_seen_at > self.stale_after
        )
        return WorkerSummary(
            worker_id=record.worker_id,
            worker_type=record.worker_type,
            health_state=WorkerHealthState.OFFLINE if stale else record.health_state,
            last_seen_at=record.last_seen_at,
            version_no=record.version_no,
            stale=stale,
        )


def utc_now() -> datetime:
    """Composition-friendly clock; deterministic tests inject their own now."""
    return datetime.now(UTC)
