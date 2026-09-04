from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.device.models import DeviceRecord


class DeviceRepositoryConflictError(RuntimeError):
    pass


class DeviceRepository(Protocol):
    def get(self, device_id: str) -> DeviceRecord | None: ...

    def add(self, device: DeviceRecord) -> None: ...

    def replace(self, device: DeviceRecord, *, expected_version: int) -> None: ...
