from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.worker_registry.models import (
    WORKER_REPORTABLE_HEALTH_STATES,
    WorkerHealthState,
    WorkerRecord,
    WorkerType,
)
from mtaffiliate.ports.repositories.worker_registry import (
    UnknownWorkerError,
    WorkerRegistrationConflictError,
)

from .models import WorkersRow


def _refresh_health_state(existing: WorkersRow) -> str:
    """Registration refreshes liveness but must not resurrect a Back Office disable."""
    if WorkerHealthState(existing.health_state) not in WORKER_REPORTABLE_HEALTH_STATES:
        return existing.health_state
    return WorkerHealthState.ONLINE_IDLE.value


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SQLAlchemyWorkerRegistryRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: WorkersRow) -> WorkerRecord:
        return WorkerRecord(
            worker_id=row.worker_id,
            worker_type=WorkerType(row.worker_type),
            installation_id=row.installation_id,
            host_id=row.host_id,
            version=row.version,
            capabilities=json.loads(row.capabilities) if row.capabilities else [],
            health_state=WorkerHealthState(row.health_state),
            enrolled_at=_as_utc(row.enrolled_at),
            last_seen_at=_as_utc(row.last_seen_at),
            version_no=row.version_no,
        )

    @staticmethod
    def _row(record: WorkerRecord) -> WorkersRow:
        return WorkersRow(
            worker_id=record.worker_id,
            worker_type=record.worker_type.value,
            installation_id=record.installation_id,
            host_id=record.host_id,
            version=record.version,
            capabilities=json.dumps(record.capabilities, separators=(",", ":")),
            health_state=record.health_state.value,
            enrolled_at=record.enrolled_at,
            last_seen_at=record.last_seen_at,
            version_no=record.version_no,
        )

    def _register_once(self, record: WorkerRecord) -> WorkerRecord:
        with self._session_factory() as session, session.begin():
            existing = session.get(WorkersRow, record.worker_id)
            if existing is None:
                session.add(self._row(record))
                return record
            if existing.installation_id != record.installation_id:
                raise WorkerRegistrationConflictError(
                    f"worker_id collision: {record.worker_id}"
                )
            existing.version = record.version
            existing.host_id = record.host_id
            existing.capabilities = json.dumps(record.capabilities, separators=(",", ":"))
            existing.health_state = _refresh_health_state(existing)
            existing.last_seen_at = record.last_seen_at
            existing.version_no += 1
            return self._to_domain(existing)

    def register(self, record: WorkerRecord) -> WorkerRecord:
        """Insert-or-refresh one enrollment; retry once after a unique race.

        Retrying the whole transaction keeps the conflict decision atomic with
        the read that detected it.
        """
        try:
            return self._register_once(record)
        except IntegrityError:
            return self._register_once(record)

    def record_heartbeat(
        self,
        worker_id: str,
        *,
        health_state: WorkerHealthState,
        seen_at: datetime,
    ) -> WorkerRecord:
        with self._session_factory() as session, session.begin():
            existing = session.get(WorkersRow, worker_id)
            if existing is None:
                raise UnknownWorkerError(f"unknown worker: {worker_id}")
            existing.health_state = health_state.value
            existing.last_seen_at = seen_at
            existing.version_no += 1
            return self._to_domain(existing)

    def get(self, worker_id: str) -> WorkerRecord | None:
        with self._session_factory() as session:
            row = session.get(WorkersRow, worker_id)
            return None if row is None else self._to_domain(row)

    def list(self) -> list[WorkerRecord]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(WorkersRow).order_by(WorkersRow.worker_id)
            ).all()
        return [self._to_domain(row) for row in rows]
