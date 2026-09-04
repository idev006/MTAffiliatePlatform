from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import uuid4

from mtaffiliate.domain.job.models import JobCheckpoint, JobRecord, JobState
from mtaffiliate.ports.repositories.job import JobRepository


class InvalidJobTransitionError(RuntimeError):
    pass


class StaleLeaseError(RuntimeError):
    pass


class IdempotencyConflictError(RuntimeError):
    pass


class SharedJobEngine:
    """Headless canonical lifecycle authority for bounded worker jobs."""

    def __init__(
        self,
        repository: JobRepository,
        *,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository
        self._token_factory = token_factory or (lambda: str(uuid4()))

    def create_job(
        self,
        *,
        job_id: str,
        job_type: str,
        domain: str,
        payload_ref: str,
        idempotency_key: str,
        created_at: datetime,
        priority: int = 0,
        capability_requirements: tuple[str, ...] = (),
    ) -> JobRecord:
        existing = self.repository.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            same_semantics = (
                existing.job_type == job_type
                and existing.domain == domain
                and existing.payload_ref == payload_ref
                and existing.priority == priority
                and existing.capability_requirements == capability_requirements
            )
            if not same_semantics:
                raise IdempotencyConflictError(
                    f"idempotency key reused with different job semantics: {idempotency_key}"
                )
            return existing

        job = JobRecord(
            job_id=job_id,
            job_type=job_type,
            domain=domain,
            payload_ref=payload_ref,
            priority=priority,
            idempotency_key=idempotency_key,
            capability_requirements=capability_requirements,
            created_at=created_at,
            updated_at=created_at,
        )
        self.repository.add(job)
        return job

    def queue_job(self, job_id: str, *, at: datetime) -> JobRecord:
        job = self._require(job_id)
        self._require_state(job, {JobState.CREATED})
        return self._replace(job, at=at, state=JobState.QUEUED)

    def lease_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        worker_capabilities: set[str],
        at: datetime,
        lease_for: timedelta,
    ) -> JobRecord:
        if lease_for <= timedelta(0):
            raise ValueError("lease_for must be positive")
        job = self._require(job_id)
        self._require_state(job, {JobState.QUEUED})
        missing = set(job.capability_requirements) - worker_capabilities
        if missing:
            raise InvalidJobTransitionError(
                f"worker lacks required capabilities: {sorted(missing)}"
            )
        return self._replace(
            job,
            at=at,
            state=JobState.LEASED,
            assigned_worker_id=worker_id,
            lease_token=self._token_factory(),
            lease_until=at + lease_for,
            attempt_no=job.attempt_no + 1,
        )

    def start_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        at: datetime,
    ) -> JobRecord:
        job = self._require_active_lease(
            job_id, worker_id=worker_id, lease_token=lease_token, at=at
        )
        self._require_state(job, {JobState.LEASED})
        return self._replace(job, at=at, state=JobState.IN_PROGRESS)

    def renew_lease(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        at: datetime,
        lease_for: timedelta,
    ) -> JobRecord:
        if lease_for <= timedelta(0):
            raise ValueError("lease_for must be positive")
        job = self._require_active_lease(
            job_id, worker_id=worker_id, lease_token=lease_token, at=at
        )
        self._require_state(
            job, {JobState.LEASED, JobState.IN_PROGRESS, JobState.VERIFYING}
        )
        return self._replace(job, at=at, lease_until=at + lease_for)

    def record_checkpoint(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        checkpoint_type: str,
        payload: dict[str, object],
        at: datetime,
    ) -> JobRecord:
        job = self._require_active_lease(
            job_id, worker_id=worker_id, lease_token=lease_token, at=at
        )
        self._require_state(job, {JobState.IN_PROGRESS})
        checkpoint = JobCheckpoint(
            checkpoint_type=checkpoint_type,
            payload=payload,
            worker_id=worker_id,
            created_at=at,
            job_version=job.job_version + 1,
        )
        return self._replace(job, at=at, checkpoint=checkpoint)

    def pause_job(self, job_id: str, *, at: datetime) -> JobRecord:
        job = self._require(job_id)
        self._require_state(job, {JobState.LEASED, JobState.IN_PROGRESS})
        return self._replace(
            job,
            at=at,
            state=JobState.PAUSED,
            assigned_worker_id=None,
            lease_token=None,
            lease_until=None,
        )

    def resume_job(self, job_id: str, *, at: datetime) -> JobRecord:
        job = self._require(job_id)
        self._require_state(job, {JobState.PAUSED})
        return self._replace(job, at=at, state=JobState.QUEUED)

    def begin_verification(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        at: datetime,
    ) -> JobRecord:
        job = self._require_active_lease(
            job_id, worker_id=worker_id, lease_token=lease_token, at=at
        )
        self._require_state(job, {JobState.IN_PROGRESS})
        return self._replace(job, at=at, state=JobState.VERIFYING)

    def complete_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        at: datetime,
    ) -> JobRecord:
        job = self._require_active_lease(
            job_id, worker_id=worker_id, lease_token=lease_token, at=at
        )
        self._require_state(job, {JobState.VERIFYING})
        return self._replace(
            job,
            at=at,
            state=JobState.COMPLETED,
            assigned_worker_id=None,
            lease_token=None,
            lease_until=None,
        )

    def mark_needs_human(
        self,
        job_id: str,
        *,
        failure_code: str,
        detail: str | None,
        at: datetime,
    ) -> JobRecord:
        job = self._require(job_id)
        self._require_state(
            job,
            {
                JobState.QUEUED,
                JobState.LEASED,
                JobState.IN_PROGRESS,
                JobState.PAUSED,
                JobState.VERIFYING,
            },
        )
        return self._replace(
            job,
            at=at,
            state=JobState.NEEDS_HUMAN,
            assigned_worker_id=None,
            lease_token=None,
            lease_until=None,
            failure_code=failure_code,
            failure_detail=detail,
        )

    def cancel_job(self, job_id: str, *, at: datetime) -> JobRecord:
        job = self._require(job_id)
        self._require_state(
            job,
            {JobState.CREATED, JobState.QUEUED, JobState.PAUSED},
        )
        return self._replace(job, at=at, state=JobState.CANCELLED)

    def requeue_expired(
        self,
        job_id: str,
        *,
        at: datetime,
        safe_to_reassign: bool,
    ) -> JobRecord:
        job = self._require(job_id)
        self._require_state(
            job, {JobState.LEASED, JobState.IN_PROGRESS, JobState.VERIFYING}
        )
        if job.lease_until is None or at <= job.lease_until:
            raise InvalidJobTransitionError("job lease has not expired")
        if not safe_to_reassign:
            return self.mark_needs_human(
                job_id,
                failure_code="LEASE_EXPIRED_UNSAFE_TO_REASSIGN",
                detail="lease expired without proof that replay/reassignment is safe",
                at=at,
            )
        return self._replace(
            job,
            at=at,
            state=JobState.QUEUED,
            assigned_worker_id=None,
            lease_token=None,
            lease_until=None,
        )

    def _require(self, job_id: str) -> JobRecord:
        job = self.repository.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    @staticmethod
    def _require_state(job: JobRecord, allowed: set[JobState]) -> None:
        if job.state not in allowed:
            raise InvalidJobTransitionError(
                f"job {job.job_id} is {job.state}; expected one of "
                f"{sorted(state.value for state in allowed)}"
            )

    def _require_active_lease(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        at: datetime,
    ) -> JobRecord:
        job = self._require(job_id)
        if job.assigned_worker_id != worker_id or job.lease_token != lease_token:
            raise StaleLeaseError("worker or lease token does not own this job")
        if job.lease_until is None or at > job.lease_until:
            raise StaleLeaseError("job lease has expired")
        return job

    def _replace(self, job: JobRecord, *, at: datetime, **changes: object) -> JobRecord:
        updated = job.model_copy(
            update={
                **changes,
                "job_version": job.job_version + 1,
                "updated_at": at,
            }
        )
        self.repository.replace(updated, expected_version=job.job_version)
        return updated
