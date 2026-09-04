from __future__ import annotations

from datetime import UTC

from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.device.models import DeviceRecord
from mtaffiliate.ports.repositories.device import DeviceRepositoryConflictError

from .models import Program3DeviceRow


class SQLAlchemyDeviceRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: Program3DeviceRow) -> DeviceRecord:
        lease_expires_at = row.lease_expires_at
        if lease_expires_at is not None and lease_expires_at.tzinfo is None:
            lease_expires_at = lease_expires_at.replace(tzinfo=UTC)
        return DeviceRecord(
            device_id=row.device_id,
            adb_serial=row.adb_serial,
            host_id=row.host_id,
            status=row.status,
            worker_id=row.worker_id,
            lease_expires_at=lease_expires_at,
            version_no=row.version_no,
        )

    def get(self, device_id: str) -> DeviceRecord | None:
        with self._session_factory() as session:
            row = session.get(Program3DeviceRow, device_id)
            return None if row is None else self._to_domain(row)

    def add(self, device: DeviceRecord) -> None:
        with self._session_factory() as session, session.begin():
            if session.get(Program3DeviceRow, device.device_id) is not None:
                raise DeviceRepositoryConflictError(
                    f"device already exists: {device.device_id}"
                )
            session.add(
                Program3DeviceRow(
                    device_id=device.device_id,
                    adb_serial=device.adb_serial,
                    host_id=device.host_id,
                    status=device.status,
                    worker_id=device.worker_id,
                    lease_expires_at=device.lease_expires_at,
                    version_no=device.version_no,
                )
            )

    def replace(self, device: DeviceRecord, *, expected_version: int) -> None:
        with self._session_factory() as session, session.begin():
            row = session.get(Program3DeviceRow, device.device_id)
            if row is None:
                raise DeviceRepositoryConflictError(f"unknown device: {device.device_id}")
            if row.version_no != expected_version:
                raise DeviceRepositoryConflictError(
                    f"stale device version: {device.device_id}; "
                    f"expected {expected_version}, current {row.version_no}"
                )
            if device.version_no != expected_version + 1:
                raise DeviceRepositoryConflictError(
                    f"replacement device version must be {expected_version + 1}"
                )
            row.adb_serial = device.adb_serial
            row.host_id = device.host_id
            row.status = device.status
            row.worker_id = device.worker_id
            row.lease_expires_at = device.lease_expires_at
            row.version_no = device.version_no
