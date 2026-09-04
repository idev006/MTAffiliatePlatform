from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.device import InMemoryDeviceRepository
from mtaffiliate.application.program3_device import Program3DeviceService
from mtaffiliate.domain.device.models import DeviceRecord
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.ports.repositories.device import DeviceRepositoryConflictError

NOW = datetime(2026, 9, 5, 2, 0, tzinfo=UTC)


def service() -> Program3DeviceService:
    return Program3DeviceService(InMemoryDeviceRepository(), DeviceHostEngine())


def test_register_claim_renew_release_and_recover_expired_device() -> None:
    svc = service()
    registered = svc.register(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    assert registered.version_no == 1
    assert registered.worker_id is None

    refreshed = svc.register(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    assert refreshed.version_no == 2

    claimed = svc.claim(
        "device-1",
        worker_id="worker-1",
        at=NOW,
        lease_for=timedelta(minutes=5),
    )
    assert claimed.worker_id == "worker-1"
    assert claimed.lease_expires_at == NOW + timedelta(minutes=5)
    assert svc.assert_active_ownership("device-1", worker_id="worker-1", at=NOW) == claimed

    with pytest.raises(ValueError, match="DEVICE_OWNED_BY_ACTIVE_WORKER"):
        svc.claim(
            "device-1",
            worker_id="worker-2",
            at=NOW + timedelta(minutes=1),
            lease_for=timedelta(minutes=5),
        )

    renewed = svc.renew(
        "device-1",
        worker_id="worker-1",
        at=NOW + timedelta(minutes=1),
        lease_for=timedelta(minutes=10),
    )
    assert renewed.lease_expires_at == NOW + timedelta(minutes=11)

    with pytest.raises(ValueError, match="DEVICE_NOT_OWNED_BY_WORKER"):
        svc.release("device-1", worker_id="worker-2")

    released = svc.release("device-1", worker_id="worker-1")
    assert released.worker_id is None
    assert released.lease_expires_at is None

    first = svc.claim(
        "device-1",
        worker_id="worker-1",
        at=NOW + timedelta(minutes=20),
        lease_for=timedelta(minutes=1),
    )
    assert first.worker_id == "worker-1"
    reassigned = svc.claim(
        "device-1",
        worker_id="worker-2",
        at=NOW + timedelta(minutes=22),
        lease_for=timedelta(minutes=3),
    )
    assert reassigned.worker_id == "worker-2"


def test_device_identity_health_and_lease_fail_closed() -> None:
    svc = service()
    svc.register(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    with pytest.raises(ValueError, match="device identity conflict"):
        svc.register(
            device_id="device-1",
            adb_serial="different",
            host_id="host-1",
            status="ONLINE",
        )
    with pytest.raises(KeyError):
        svc.claim(
            "missing",
            worker_id="worker-1",
            at=NOW,
            lease_for=timedelta(minutes=1),
        )
    with pytest.raises(ValueError, match="positive"):
        svc.claim(
            "device-1",
            worker_id="worker-1",
            at=NOW,
            lease_for=timedelta(0),
        )
    with pytest.raises(ValueError, match="positive"):
        svc.renew(
            "device-1",
            worker_id="worker-1",
            at=NOW,
            lease_for=timedelta(0),
        )

    for device_id, status, expected in [
        ("unauthorized", "UNAUTHORIZED", "ADB_UNAUTHORIZED_NEEDS_HUMAN"),
        ("offline", "OFFLINE", "DEVICE_NOT_ONLINE"),
        ("missing-status", "MISSING", "DEVICE_NOT_ONLINE"),
    ]:
        svc.register(
            device_id=device_id,
            adb_serial=f"serial-{device_id}",
            host_id="host-1",
            status=status,
        )
        with pytest.raises(ValueError, match=expected):
            svc.claim(
                device_id,
                worker_id="worker-1",
                at=NOW,
                lease_for=timedelta(minutes=1),
            )

    svc.claim(
        "device-1",
        worker_id="worker-1",
        at=NOW,
        lease_for=timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="DEVICE_NOT_OWNED_BY_WORKER"):
        svc.assert_active_ownership(
            "device-1",
            worker_id="worker-2",
            at=NOW + timedelta(seconds=30),
        )
    with pytest.raises(ValueError, match="DEVICE_OWNERSHIP_LEASE_EXPIRED"):
        svc.assert_active_ownership(
            "device-1",
            worker_id="worker-1",
            at=NOW + timedelta(minutes=1),
        )


def test_device_admission_reports_current_assignment_policy() -> None:
    svc = service()
    svc.register(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    available = svc.admission("device-1", worker_id="worker-1", at=NOW)
    assert available.allowed is True
    assert available.reason == "DEVICE_AVAILABLE"

    svc.claim(
        "device-1",
        worker_id="worker-1",
        at=NOW,
        lease_for=timedelta(minutes=5),
    )
    same_worker = svc.admission("device-1", worker_id="worker-1", at=NOW)
    assert same_worker.allowed is True
    other_worker = svc.admission("device-1", worker_id="worker-2", at=NOW)
    assert other_worker.allowed is False


def test_inmemory_device_repository_enforces_optimistic_versions() -> None:
    repo = InMemoryDeviceRepository()
    device = DeviceRecord(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    assert repo.get("missing") is None
    repo.add(device)
    with pytest.raises(DeviceRepositoryConflictError, match="already exists"):
        repo.add(device)

    updated = device.model_copy(update={"version_no": 2})
    repo.replace(updated, expected_version=1)
    assert repo.get("device-1") == updated

    with pytest.raises(DeviceRepositoryConflictError, match="stale device version"):
        repo.replace(updated.model_copy(update={"version_no": 3}), expected_version=1)
    with pytest.raises(DeviceRepositoryConflictError, match="replacement device version"):
        repo.replace(updated.model_copy(update={"version_no": 4}), expected_version=2)
    with pytest.raises(DeviceRepositoryConflictError, match="unknown device"):
        repo.replace(
            DeviceRecord(
                device_id="unknown",
                adb_serial="unknown",
                host_id="host",
                status="ONLINE",
                version_no=2,
            ),
            expected_version=1,
        )
