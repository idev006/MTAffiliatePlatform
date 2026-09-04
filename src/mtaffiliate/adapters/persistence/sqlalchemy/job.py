from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.job.models import JobCheckpoint, JobEvent, JobRecord, JobState
from mtaffiliate.ports.repositories.job import JobRepositoryConflictError

from .models import JobEventsRow, JobsRow


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SQLAlchemyJobRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _checkpoint_json(checkpoint: JobCheckpoint | None) -> str | None:
        if checkpoint is None:
            return None
        return checkpoint.model_dump_json()

    @staticmethod
    def _checkpoint(value: str | None) -> JobCheckpoint | None:
        if value is None:
            return None
        return JobCheckpoint.model_validate_json(value)

    @classmethod
    def _to_domain(cls, row: JobsRow) -> JobRecord:
        return JobRecord(
            job_id=row.job_id,
            job_type=row.job_type,
            domain=row.domain,
            payload_ref=row.payload_ref,
            priority=row.priority,
            idempotency_key=row.idempotency_key,
            capability_requirements=tuple(json.loads(row.capability_requirements)),
            state=JobState(row.state),
            job_version=row.job_version,
            assigned_worker_id=row.assigned_worker_id,
            lease_token=row.lease_token,
            lease_until=_as_utc(row.lease_until),
            attempt_no=row.attempt_no,
            checkpoint=cls._checkpoint(row.checkpoint_json),
            created_at=_as_utc(row.created_at),
            updated_at=_as_utc(row.updated_at),
            failure_code=row.failure_code,
            failure_detail=row.failure_detail,
        )

    @staticmethod
    def _row(job: JobRecord) -> JobsRow:
        return JobsRow(
            job_id=job.job_id,
            job_type=job.job_type,
            domain=job.domain,
            payload_ref=job.payload_ref,
            priority=job.priority,
            idempotency_key=job.idempotency_key,
            capability_requirements=json.dumps(
                list(job.capability_requirements), separators=(",", ":")
            ),
            state=job.state.value,
            job_version=job.job_version,
            assigned_worker_id=job.assigned_worker_id,
            lease_token=job.lease_token,
            lease_until=job.lease_until,
            attempt_no=job.attempt_no,
            checkpoint_json=SQLAlchemyJobRepository._checkpoint_json(job.checkpoint),
            created_at=job.created_at,
            updated_at=job.updated_at,
            failure_code=job.failure_code,
            failure_detail=job.failure_detail,
        )

    @staticmethod
    def _event_row(event: JobEvent) -> JobEventsRow:
        return JobEventsRow(
            job_id=event.job_id,
            event_type=event.event_type,
            job_version=event.job_version,
            emitted_at=event.emitted_at,
            worker_id=event.worker_id,
            detail=event.detail,
        )

    @staticmethod
    def _event_domain(row: JobEventsRow) -> JobEvent:
        emitted_at = _as_utc(row.emitted_at)
        assert emitted_at is not None
        return JobEvent(
            event_type=row.event_type,
            job_id=row.job_id,
            job_version=row.job_version,
            emitted_at=emitted_at,
            worker_id=row.worker_id,
            detail=row.detail,
        )

    def get(self, job_id: str) -> JobRecord | None:
        with self._session_factory() as session:
            row = session.get(JobsRow, job_id)
            return None if row is None else self._to_domain(row)

    def get_by_idempotency_key(self, idempotency_key: str) -> JobRecord | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(JobsRow).where(JobsRow.idempotency_key == idempotency_key)
            )
            return None if row is None else self._to_domain(row)

    def add_with_event(self, job: JobRecord, event: JobEvent) -> None:
        if event.job_id != job.job_id or event.job_version != job.job_version:
            raise ValueError("job event must match added job identity/version")
        try:
            with self._session_factory() as session, session.begin():
                session.add(self._row(job))
                session.add(self._event_row(event))
                session.flush()
        except IntegrityError as exc:
            raise JobRepositoryConflictError(
                f"job/idempotency/event conflict: {job.job_id}"
            ) from exc

    def replace_with_event(
        self,
        job: JobRecord,
        event: JobEvent,
        *,
        expected_version: int,
    ) -> None:
        if event.job_id != job.job_id or event.job_version != job.job_version:
            raise ValueError("job event must match replacement job identity/version")

        values = {
            "job_type": job.job_type,
            "domain": job.domain,
            "payload_ref": job.payload_ref,
            "priority": job.priority,
            "idempotency_key": job.idempotency_key,
            "capability_requirements": json.dumps(
                list(job.capability_requirements), separators=(",", ":")
            ),
            "state": job.state.value,
            "job_version": job.job_version,
            "assigned_worker_id": job.assigned_worker_id,
            "lease_token": job.lease_token,
            "lease_until": job.lease_until,
            "attempt_no": job.attempt_no,
            "checkpoint_json": self._checkpoint_json(job.checkpoint),
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "failure_code": job.failure_code,
            "failure_detail": job.failure_detail,
        }
        try:
            with self._session_factory() as session, session.begin():
                result = session.execute(
                    update(JobsRow)
                    .where(
                        JobsRow.job_id == job.job_id,
                        JobsRow.job_version == expected_version,
                    )
                    .values(**values)
                )
                if result.rowcount != 1:
                    raise JobRepositoryConflictError(
                        f"stale job version: {job.job_id}:{expected_version}"
                    )
                session.add(self._event_row(event))
                session.flush()
        except IntegrityError as exc:
            raise JobRepositoryConflictError(
                f"job/event conflict: {job.job_id}:{job.job_version}"
            ) from exc

    def list_jobs(self) -> list[JobRecord]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(JobsRow).order_by(
                    JobsRow.priority.desc(),
                    JobsRow.created_at,
                    JobsRow.job_id,
                )
            ).all()
        return [self._to_domain(row) for row in rows]

    def list_events(self, job_id: str) -> list[JobEvent]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(JobEventsRow)
                .where(JobEventsRow.job_id == job_id)
                .order_by(JobEventsRow.job_version)
            ).all()
        return [self._event_domain(row) for row in rows]
