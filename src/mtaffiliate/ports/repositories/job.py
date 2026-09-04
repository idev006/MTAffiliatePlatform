from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.job.models import JobRecord


class JobRepository(Protocol):
    def get(self, job_id: str) -> JobRecord | None: ...

    def get_by_idempotency_key(self, idempotency_key: str) -> JobRecord | None: ...

    def add(self, job: JobRecord) -> None: ...

    def replace(self, job: JobRecord, *, expected_version: int) -> None: ...

    def list_jobs(self) -> list[JobRecord]: ...
