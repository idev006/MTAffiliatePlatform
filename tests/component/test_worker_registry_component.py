from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
    InMemoryWorkerRegistryRepository,
)
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.domain.worker_registry.models import (
    WorkerHealthState,
    WorkerRecord,
    WorkerRegistration,
    WorkerType,
)
from mtaffiliate.ports.repositories.worker_registry import (
    UnknownWorkerError,
    WorkerRegistrationConflictError,
)

START = datetime(2026, 9, 4, 10, 0, 0, tzinfo=UTC)


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


def registry_service(*, stale_after: timedelta = timedelta(seconds=90)) -> WorkerRegistryService:
    return WorkerRegistryService(
        InMemoryWorkerRegistryRepository(),
        stale_after=stale_after,
    )


def test_register_creates_online_idle_record() -> None:
    registry = registry_service()
    record = registry.register(registration(), seen_at=START)

    assert record.worker_id == "worker-01"
    assert record.health_state == WorkerHealthState.ONLINE_IDLE
    assert record.enrolled_at == START
    assert record.last_seen_at == START
    assert record.version_no == 1
    assert record.capabilities == ["collector:shopee-current-page-lab-v2"]


def test_re_register_same_installation_refreshes_and_bumps_version() -> None:
    registry = registry_service()
    registry.register(registration(), seen_at=START)
    refreshed = registry.register(
        registration(
            version="0.2.0",
            capabilities=["collector:shopee-current-page-lab-v3"],
        ),
        seen_at=START + timedelta(minutes=5),
    )

    assert refreshed.version == "0.2.0"
    assert refreshed.capabilities == ["collector:shopee-current-page-lab-v3"]
    assert refreshed.version_no == 2
    assert refreshed.enrolled_at == START
    assert refreshed.last_seen_at == START + timedelta(minutes=5)
    assert refreshed.health_state == WorkerHealthState.ONLINE_IDLE


def test_re_register_with_different_installation_conflicts() -> None:
    registry = registry_service()
    registry.register(registration(), seen_at=START)
    with pytest.raises(WorkerRegistrationConflictError):
        registry.register(registration(installation_id="other-install"), seen_at=START)


def test_registration_does_not_resurrect_disabled_worker() -> None:
    repository = InMemoryWorkerRegistryRepository()
    registry = WorkerRegistryService(repository, stale_after=timedelta(seconds=90))
    repository.register(
        WorkerRecord(
            worker_id="worker-01",
            worker_type=WorkerType.DISCOVERY_BROWSER_WORKER,
            installation_id="install-1",
            version="0.1.9",
            capabilities=[],
            health_state=WorkerHealthState.DISABLED,
            enrolled_at=START,
            last_seen_at=START,
            version_no=1,
        )
    )
    refreshed = registry.register(registration(), seen_at=START + timedelta(minutes=1))
    assert refreshed.health_state == WorkerHealthState.DISABLED


def test_heartbeat_updates_state_and_version_for_registered_worker() -> None:
    registry = registry_service()
    registry.register(registration(), seen_at=START)
    beaten = registry.record_heartbeat(
        "worker-01",
        health_state=WorkerHealthState.ONLINE_BUSY,
        seen_at=START + timedelta(seconds=30),
    )

    assert beaten.health_state == WorkerHealthState.ONLINE_BUSY
    assert beaten.last_seen_at == START + timedelta(seconds=30)
    assert beaten.version_no == 2


def test_heartbeat_for_unknown_worker_fails_closed() -> None:
    registry = registry_service()
    with pytest.raises(UnknownWorkerError):
        registry.record_heartbeat(
            "never-registered",
            health_state=WorkerHealthState.ONLINE_IDLE,
            seen_at=START,
        )


def test_summary_derives_offline_when_heartbeat_is_stale() -> None:
    registry = registry_service(stale_after=timedelta(seconds=10))
    registry.register(registration(), seen_at=START)

    fresh = registry.summary("worker-01", now=START + timedelta(seconds=9))
    assert fresh is not None
    assert fresh.health_state == WorkerHealthState.ONLINE_IDLE
    assert fresh.stale is False

    stale = registry.summary("worker-01", now=START + timedelta(seconds=11))
    assert stale is not None
    assert stale.health_state == WorkerHealthState.OFFLINE
    assert stale.stale is True


def test_summary_never_overrides_back_office_states_with_staleness() -> None:
    repository = InMemoryWorkerRegistryRepository()
    registry = WorkerRegistryService(repository, stale_after=timedelta(seconds=10))
    repository.register(
        WorkerRecord(
            worker_id="worker-02",
            worker_type=WorkerType.AFFILIATE_BROWSER_WORKER,
            installation_id="install-2",
            version="1.0.0",
            capabilities=[],
            health_state=WorkerHealthState.DISABLED,
            enrolled_at=START,
            last_seen_at=START,
            version_no=1,
        )
    )

    summary = registry.summary("worker-02", now=START + timedelta(hours=1))
    assert summary is not None
    assert summary.health_state == WorkerHealthState.DISABLED
    assert summary.stale is False


def test_summaries_are_sorted_and_include_all_workers() -> None:
    registry = registry_service()
    registry.register(registration(worker_id="worker-b"), seen_at=START)
    registry.register(registration(worker_id="worker-a"), seen_at=START)

    assert [item.worker_id for item in registry.summaries(now=START)] == [
        "worker-a",
        "worker-b",
    ]


def test_summary_returns_none_for_unknown_worker() -> None:
    registry = registry_service()
    assert registry.summary("missing", now=START) is None
