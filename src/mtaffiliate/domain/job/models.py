from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobState(StrEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    LEASED = "LEASED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    CANCELLED = "CANCELLED"


class JobCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    checkpoint_type: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    worker_id: str = Field(min_length=1)
    created_at: datetime
    job_version: int = Field(ge=1)


class JobRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str = Field(min_length=1)
    job_type: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    payload_ref: str = Field(min_length=1)
    priority: int = 0
    idempotency_key: str = Field(min_length=1)
    capability_requirements: tuple[str, ...] = ()
    state: JobState = JobState.CREATED
    job_version: int = Field(default=1, ge=1)
    assigned_worker_id: str | None = None
    lease_token: str | None = None
    lease_until: datetime | None = None
    attempt_no: int = Field(default=0, ge=0)
    checkpoint: JobCheckpoint | None = None
    created_at: datetime
    updated_at: datetime
    failure_code: str | None = None
    failure_detail: str | None = None

    @model_validator(mode="after")
    def validate_lease_shape(self) -> JobRecord:
        lease_fields = (
            self.assigned_worker_id,
            self.lease_token,
            self.lease_until,
        )
        populated = [value is not None for value in lease_fields]
        if any(populated) and not all(populated):
            raise ValueError("lease owner, token and expiry must be populated together")
        if self.state in {JobState.LEASED, JobState.IN_PROGRESS, JobState.VERIFYING}:
            if not all(populated):
                raise ValueError(f"{self.state} requires an active lease")
        return self
