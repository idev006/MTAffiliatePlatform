from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread

import pytest
from sqlalchemy.exc import IntegrityError

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import build_engine, build_session_factory
from mtaffiliate.adapters.persistence.sqlalchemy.worker_registry import (
    SQLAlchemyWorkerRegistryRepository,
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

pytestmark = pytest.mark.integration

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


def registry_service(sessions) -> WorkerRegistryService:
    return WorkerRegistryService(
        SQLAlchemyWorkerRegistryRepository(sessions),
        stale_after=timedelta(seconds=90),
    )


def test_register_heartbeat_and_read_over_sqlite(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)

    service = registry_service(sessions)
    registered = service.register(registration(), seen_at=START)
    assert registered.version_no == 1
    assert registered.health_state == WorkerHealthState.ONLINE_IDLE
    assert registered.capabilities == ["collector:shopee-current-page-lab-v2"]

    beaten = service.record_heartbeat(
        "worker-01",
        health_state=WorkerHealthState.DEGRADED,
        seen_at=START + timedelta(seconds=30),
    )
    assert beaten.version_no == 2
    assert beaten.health_state == WorkerHealthState.DEGRADED

    summary = service.summary("worker-01", now=START + timedelta(seconds=40))
    assert summary is not None
    assert summary.health_state == WorkerHealthState.DEGRADED
    assert summary.stale is False

    stale = service.summary("worker-01", now=START + timedelta(minutes=5))
    assert stale is not None
    assert stale.health_state == WorkerHealthState.OFFLINE
    engine.dispose()


def test_registry_survives_engine_recomposition(tmp_path) -> None:
    url = "sqlite:///data/registry.db"

    first_engine = build_engine(url, project_root=tmp_path)
    Base.metadata.create_all(first_engine)
    first = registry_service(build_session_factory(first_engine))
    first.register(registration(), seen_at=START)
    first_engine.dispose()

    restarted = registry_service(build_session_factory(build_engine(url, project_root=tmp_path)))
    record = restarted.repository.get("worker-01")
    assert record is not None
    assert record.version_no == 1
    assert record.enrolled_at == START

    beaten = restarted.record_heartbeat(
        "worker-01",
        health_state=WorkerHealthState.ONLINE_IDLE,
        seen_at=START + timedelta(minutes=1),
    )
    assert beaten.version_no == 2
    assert beaten.last_seen_at == START + timedelta(minutes=1)


def test_re_register_same_installation_refreshes_over_sqlite(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    service = registry_service(build_session_factory(engine))

    first = service.register(registration(), seen_at=START)
    assert first.version_no == 1

    refreshed = service.register(
        registration(
            version="0.2.0",
            capabilities=["collector:shopee-current-page-lab-v3"],
            host_id="host-1",
        ),
        seen_at=START + timedelta(minutes=1),
    )
    assert refreshed.version_no == 2
    assert refreshed.version == "0.2.0"
    assert refreshed.host_id == "host-1"
    assert refreshed.capabilities == ["collector:shopee-current-page-lab-v3"]
    assert refreshed.enrolled_at == START
    assert refreshed.last_seen_at == START + timedelta(minutes=1)
    assert refreshed.health_state == WorkerHealthState.ONLINE_IDLE
    engine.dispose()


def test_re_register_does_not_resurrect_disabled_worker_over_sqlite(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    service = registry_service(sessions)
    service.repository.register(
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

    refreshed = service.register(registration(), seen_at=START + timedelta(minutes=1))
    assert refreshed.health_state == WorkerHealthState.DISABLED
    assert refreshed.version_no == 2
    engine.dispose()


def test_register_retries_once_after_unique_race(tmp_path, monkeypatch) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    repository = SQLAlchemyWorkerRegistryRepository(build_session_factory(engine))
    original = repository._register_once
    attempts = {"count": 0}

    def racy(record: WorkerRecord) -> WorkerRecord:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise IntegrityError("INSERT", {}, Exception("simulated unique race"))
        return original(record)

    monkeypatch.setattr(repository, "_register_once", racy)

    record = repository.register(
        WorkerRecord(
            worker_id="worker-01",
            worker_type=WorkerType.DISCOVERY_BROWSER_WORKER,
            installation_id="install-1",
            version="0.1.9",
            capabilities=[],
            health_state=WorkerHealthState.ONLINE_IDLE,
            enrolled_at=START,
            last_seen_at=START,
            version_no=1,
        )
    )
    assert attempts["count"] == 2
    assert record.worker_id == "worker-01"
    assert record.version_no == 1
    engine.dispose()


def test_installation_conflict_survives_restart(tmp_path) -> None:
    url = "sqlite:///data/registry.db"

    first_engine = build_engine(url, project_root=tmp_path)
    Base.metadata.create_all(first_engine)
    registry_service(build_session_factory(first_engine)).register(
        registration(), seen_at=START
    )
    first_engine.dispose()

    restarted = registry_service(build_session_factory(build_engine(url, project_root=tmp_path)))
    with pytest.raises(WorkerRegistrationConflictError):
        restarted.register(registration(installation_id="other-install"), seen_at=START)


def test_heartbeat_for_unregistered_worker_fails_closed(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    service = registry_service(build_session_factory(engine))
    with pytest.raises(UnknownWorkerError):
        service.record_heartbeat(
            "ghost",
            health_state=WorkerHealthState.ONLINE_IDLE,
            seen_at=START,
        )
    engine.dispose()


def test_concurrent_heartbeats_increment_version_without_lost_updates(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)

    setup = registry_service(sessions)
    for index in range(4):
        setup.register(
            registration(worker_id=f"worker-0{index}", installation_id=f"install-{index}"),
            seen_at=START,
        )

    barrier = Barrier(4)

    def heartbeat(worker_id: str) -> None:
        service = registry_service(sessions)
        barrier.wait()
        for _ in range(10):
            service.record_heartbeat(
                worker_id,
                health_state=WorkerHealthState.ONLINE_IDLE,
                seen_at=datetime.now(UTC),
            )

    threads = [Thread(target=heartbeat, args=(f"worker-0{i}",)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    checker = registry_service(sessions)
    for index in range(4):
        summary = checker.summary(f"worker-0{index}", now=datetime.now(UTC))
        assert summary is not None
        assert summary.version_no == 11
    engine.dispose()


def test_concurrent_registration_of_same_worker_id_keeps_one_owner(tmp_path) -> None:
    engine = build_engine("sqlite:///data/registry.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)

    barrier = Barrier(3)
    outcomes: list[str] = []

    def attempt(installation_id: str) -> None:
        service = registry_service(sessions)
        barrier.wait()
        try:
            service.register(
                registration(worker_id="worker-01", installation_id=installation_id),
                seen_at=START,
            )
            outcomes.append("ok")
        except WorkerRegistrationConflictError:
            outcomes.append("conflict")

    threads = [Thread(target=attempt, args=(f"install-{index}",)) for index in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(outcomes) == 3
    assert sorted(outcomes) == ["conflict", "conflict", "ok"]

    summary = registry_service(sessions).summary("worker-01", now=START)
    assert summary is not None
    engine.dispose()
