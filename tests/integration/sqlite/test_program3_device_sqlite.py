from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.device import SQLAlchemyDeviceRepository
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program3_device import Program3DeviceService
from mtaffiliate.domain.device.models import DeviceRecord
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.ports.repositories.device import DeviceRepositoryConflictError

pytestmark = pytest.mark.integration
NOW = datetime(2026, 9, 5, 2, 30, tzinfo=UTC)
URL = "sqlite:///data/program3-devices.db"


def compose(root: Path):
    engine = build_engine(URL, project_root=root)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyDeviceRepository(build_session_factory(engine))
    return engine, repo


def test_sql_device_ownership_survives_restart(tmp_path: Path) -> None:
    engine, repo = compose(tmp_path)
    service = Program3DeviceService(repo, DeviceHostEngine())
    service.register(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    claimed = service.claim(
        "device-1",
        worker_id="worker-1",
        at=NOW,
        lease_for=timedelta(minutes=5),
    )
    assert claimed.version_no == 2
    engine.dispose()

    restarted_engine, restarted_repo = compose(tmp_path)
    restored = restarted_repo.get("device-1")
    assert restored is not None
    assert restored.worker_id == "worker-1"
    assert restored.lease_expires_at == NOW + timedelta(minutes=5)
    assert restored.version_no == 2

    restarted_service = Program3DeviceService(restarted_repo, DeviceHostEngine())
    assert (
        restarted_service.assert_active_ownership(
            "device-1",
            worker_id="worker-1",
            at=NOW + timedelta(minutes=1),
        )
        == restored
    )
    restarted_engine.dispose()


def test_sql_device_repository_conflicts_are_explicit(tmp_path: Path) -> None:
    engine, repo = compose(tmp_path)
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

    updated = device.model_copy(
        update={
            "worker_id": "worker-1",
            "lease_expires_at": NOW + timedelta(minutes=5),
            "version_no": 2,
        }
    )
    repo.replace(updated, expected_version=1)
    assert repo.get("device-1") == updated

    with pytest.raises(DeviceRepositoryConflictError, match="stale device version"):
        repo.replace(
            updated.model_copy(update={"version_no": 3}),
            expected_version=1,
        )
    with pytest.raises(DeviceRepositoryConflictError, match="replacement device version"):
        repo.replace(
            updated.model_copy(update={"version_no": 4}),
            expected_version=2,
        )
    with pytest.raises(DeviceRepositoryConflictError, match="unknown device"):
        repo.replace(
            DeviceRecord(
                device_id="unknown",
                adb_serial="serial-unknown",
                host_id="host-1",
                status="ONLINE",
                version_no=2,
            ),
            expected_version=1,
        )
    engine.dispose()
