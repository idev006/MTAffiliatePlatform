from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.domain.worker_registry.models import (
    WorkerHealthState,
    WorkerRecord,
    WorkerRegistration,
    WorkerType,
)
from mtaffiliate.ports.repositories.worker_registry import WorkerRegistryRepository


class _UnusedRepository(WorkerRegistryRepository):
    """Protocol-shaped stub; service rules must reject input before storage."""

    def register(self, record: WorkerRecord) -> WorkerRecord:  # pragma: no cover
        raise AssertionError("register should not be reached")

    def record_heartbeat(self, worker_id, *, health_state, seen_at):  # pragma: no cover
        raise AssertionError("record_heartbeat should not be reached")

    def get(self, worker_id):  # pragma: no cover
        raise AssertionError("get should not be reached")

    def list(self):  # pragma: no cover
        raise AssertionError("list should not be reached")


def registration(**overrides: object) -> WorkerRegistration:
    values: dict[str, object] = {
        "worker_id": "worker-01",
        "worker_type": WorkerType.DISCOVERY_BROWSER_WORKER,
        "installation_id": "install-1",
        "version": "0.1.9",
        "capabilities": ["collector:shopee-current-page-lab-v2"],
    }
    values.update(overrides)
    return WorkerRegistration(**values)


def service() -> WorkerRegistryService:
    return WorkerRegistryService(
        _UnusedRepository(),
        stale_after=timedelta(seconds=90),
    )


def test_registration_rejects_blank_identity_fields() -> None:
    for field in ("worker_id", "installation_id", "version"):
        with pytest.raises(ValidationError):
            registration(**{field: "   "})


def test_registration_rejects_unknown_worker_type() -> None:
    with pytest.raises(ValidationError):
        registration(worker_type="ROBOT_WORKER")


def test_registration_keeps_schema_version_default() -> None:
    assert registration().schema_version == "worker-registration-v1"


def test_registration_cleans_blank_capabilities() -> None:
    reg = registration(capabilities=[" a ", "   ", "b "])
    assert reg.clean_capabilities == ["a", "b"]


def test_service_rejects_non_positive_stale_after() -> None:
    for delta in (timedelta(0), timedelta(seconds=-1)):
        with pytest.raises(ValueError):
            WorkerRegistryService(_UnusedRepository(), stale_after=delta)


def test_heartbeat_rejects_back_office_only_health_states() -> None:
    registry = service()
    for state in (WorkerHealthState.OFFLINE, WorkerHealthState.DISABLED):
        with pytest.raises(ValueError, match="may only report"):
            registry.record_heartbeat(
                "worker-01",
                health_state=state,
                seen_at=datetime(2026, 9, 4, tzinfo=UTC),
            )


def test_heartbeat_accepts_worker_reportable_states() -> None:
    registry = service()
    with pytest.raises(AssertionError, match="record_heartbeat should not be reached"):
        # State passes service validation; the stub repository proves the rule
        # boundary by failing only after the service would have called it.
        registry.record_heartbeat(
            "worker-01",
            health_state=WorkerHealthState.ONLINE_BUSY,
            seen_at=datetime(2026, 9, 4, tzinfo=UTC),
        )


def test_execution_record_requires_known_online_idle_worker() -> None:
    from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
        InMemoryWorkerRegistryRepository,
    )

    repo = InMemoryWorkerRegistryRepository()
    registry = WorkerRegistryService(repo, stale_after=timedelta(seconds=90))
    now = datetime(2026, 9, 4, tzinfo=UTC)

    with pytest.raises(KeyError):
        registry.execution_record("missing", now=now)

    registered = registry.register(registration(), seen_at=now)
    assert registry.execution_record("worker-01", now=now) == registered

    registry.record_heartbeat(
        "worker-01",
        health_state=WorkerHealthState.ONLINE_BUSY,
        seen_at=now,
    )
    with pytest.raises(ValueError, match="not eligible for a new lease"):
        registry.execution_record("worker-01", now=now)


def test_execution_record_rejects_stale_worker() -> None:
    from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
        InMemoryWorkerRegistryRepository,
    )

    repo = InMemoryWorkerRegistryRepository()
    registry = WorkerRegistryService(repo, stale_after=timedelta(seconds=1))
    seen = datetime(2026, 9, 4, tzinfo=UTC)
    registry.register(registration(), seen_at=seen)

    with pytest.raises(ValueError, match="OFFLINE"):
        registry.execution_record("worker-01", now=seen + timedelta(seconds=2))
