from __future__ import annotations

from datetime import datetime, timedelta

from mtaffiliate.domain.device.models import DeviceAdmissionDecision, DeviceRecord
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.ports.repositories.device import DeviceRepository


class Program3DeviceService:
    """Back Office authority for device registration and one-worker ownership leases."""

    def __init__(self, repository: DeviceRepository, engine: DeviceHostEngine) -> None:
        self.repository = repository
        self.engine = engine

    def register(
        self,
        *,
        device_id: str,
        adb_serial: str,
        host_id: str,
        status: str,
    ) -> DeviceRecord:
        existing = self.repository.get(device_id)
        if existing is not None:
            if existing.adb_serial != adb_serial or existing.host_id != host_id:
                raise ValueError("device identity conflict")
            updated = existing.model_copy(
                update={
                    "status": status,
                    "version_no": existing.version_no + 1,
                }
            )
            self.repository.replace(updated, expected_version=existing.version_no)
            return updated
        device = DeviceRecord(
            device_id=device_id,
            adb_serial=adb_serial,
            host_id=host_id,
            status=status,
        )
        self.repository.add(device)
        return device

    def claim(
        self,
        device_id: str,
        *,
        worker_id: str,
        at: datetime,
        lease_for: timedelta,
    ) -> DeviceRecord:
        if lease_for <= timedelta(0):
            raise ValueError("device lease_for must be positive")
        device = self._require(device_id)
        decision = self.engine.can_assign(device, worker_id=worker_id, now=at)
        if not decision.allowed:
            raise ValueError(decision.reason)
        updated = device.model_copy(
            update={
                "worker_id": worker_id,
                "lease_expires_at": at + lease_for,
                "version_no": device.version_no + 1,
            }
        )
        self.repository.replace(updated, expected_version=device.version_no)
        return updated

    def renew(
        self,
        device_id: str,
        *,
        worker_id: str,
        at: datetime,
        lease_for: timedelta,
    ) -> DeviceRecord:
        if lease_for <= timedelta(0):
            raise ValueError("device lease_for must be positive")
        device = self._require(device_id)
        self.assert_active_ownership(device_id, worker_id=worker_id, at=at)
        updated = device.model_copy(
            update={
                "lease_expires_at": at + lease_for,
                "version_no": device.version_no + 1,
            }
        )
        self.repository.replace(updated, expected_version=device.version_no)
        return updated

    def release(self, device_id: str, *, worker_id: str) -> DeviceRecord:
        device = self._require(device_id)
        if device.worker_id != worker_id:
            raise ValueError("DEVICE_NOT_OWNED_BY_WORKER")
        updated = device.model_copy(
            update={
                "worker_id": None,
                "lease_expires_at": None,
                "version_no": device.version_no + 1,
            }
        )
        self.repository.replace(updated, expected_version=device.version_no)
        return updated

    def assert_active_ownership(
        self,
        device_id: str,
        *,
        worker_id: str,
        at: datetime,
    ) -> DeviceRecord:
        device = self._require(device_id)
        if device.status == "UNAUTHORIZED":
            raise ValueError("ADB_UNAUTHORIZED_NEEDS_HUMAN")
        if device.status != "ONLINE":
            raise ValueError("DEVICE_NOT_ONLINE")
        if device.worker_id != worker_id:
            raise ValueError("DEVICE_NOT_OWNED_BY_WORKER")
        if device.lease_expires_at is None or at >= device.lease_expires_at:
            raise ValueError("DEVICE_OWNERSHIP_LEASE_EXPIRED")
        return device

    def admission(
        self,
        device_id: str,
        *,
        worker_id: str,
        at: datetime,
    ) -> DeviceAdmissionDecision:
        return self.engine.can_assign(self._require(device_id), worker_id=worker_id, now=at)

    def _require(self, device_id: str) -> DeviceRecord:
        device = self.repository.get(device_id)
        if device is None:
            raise KeyError(device_id)
        return device
