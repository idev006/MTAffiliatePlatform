from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.device.models import DeviceRecord
from mtaffiliate.ports.repositories.device import DeviceRepositoryConflictError


class InMemoryDeviceRepository:
    def __init__(self) -> None:
        self._records: dict[str, DeviceRecord] = {}
        self._lock = RLock()

    def get(self, device_id: str) -> DeviceRecord | None:
        with self._lock:
            return self._records.get(device_id)

    def add(self, device: DeviceRecord) -> None:
        with self._lock:
            if device.device_id in self._records:
                raise DeviceRepositoryConflictError(f"device already exists: {device.device_id}")
            self._records[device.device_id] = device

    def replace(self, device: DeviceRecord, *, expected_version: int) -> None:
        with self._lock:
            current = self._records.get(device.device_id)
            if current is None:
                raise DeviceRepositoryConflictError(f"unknown device: {device.device_id}")
            if current.version_no != expected_version:
                raise DeviceRepositoryConflictError(
                    f"stale device version: {device.device_id}; "
                    f"expected {expected_version}, current {current.version_no}"
                )
            if device.version_no != expected_version + 1:
                raise DeviceRepositoryConflictError(
                    f"replacement device version must be {expected_version + 1}"
                )
            self._records[device.device_id] = device
