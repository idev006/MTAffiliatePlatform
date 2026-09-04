from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.job.models import JobEvent, JobRecord


class JobRepositoryConflictError(RuntimeError):
    pass


class JobRepository(Protocol):
    def get(self, job_id: str) -> JobRecord | None: ...

    def get_by_idempotency_key(self, idempotency_key: str) -> JobRecord | None: ...

    def add_with_event(self, job: JobRecord, event: JobEvent) -> None: ...

    def replace_with_event(
        self,
        job: JobRecord,
        event: JobEvent,
        *,
        expected_version: int,
    ) -> None: ...

    def list_jobs(self) -> list[JobRecord]: ...

    def list_events(self, job_id: str) -> list[JobEvent]: ...
