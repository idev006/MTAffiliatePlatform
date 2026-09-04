from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.job.models import JobRecord


class JobRepositoryConflictError(RuntimeError):
    pass


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._by_idempotency: dict[str, str] = {}
        self._lock = RLock()

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> JobRecord | None:
        with self._lock:
            job_id = self._by_idempotency.get(idempotency_key)
            return self._jobs.get(job_id) if job_id is not None else None

    def add(self, job: JobRecord) -> None:
        with self._lock:
            if job.job_id in self._jobs:
                raise JobRepositoryConflictError(f"job already exists: {job.job_id}")
            existing = self._by_idempotency.get(job.idempotency_key)
            if existing is not None:
                raise JobRepositoryConflictError(
                    f"idempotency key already exists: {job.idempotency_key}"
                )
            self._jobs[job.job_id] = job
            self._by_idempotency[job.idempotency_key] = job.job_id

    def replace(self, job: JobRecord, *, expected_version: int) -> None:
        with self._lock:
            current = self._jobs.get(job.job_id)
            if current is None:
                raise KeyError(job.job_id)
            if current.job_version != expected_version:
                raise JobRepositoryConflictError(
                    f"stale job version: expected {expected_version}, "
                    f"actual {current.job_version}"
                )
            self._jobs[job.job_id] = job

    def list_jobs(self) -> list[JobRecord]:
        with self._lock:
            return list(self._jobs.values())
