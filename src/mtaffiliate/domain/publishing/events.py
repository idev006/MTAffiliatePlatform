from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PublishOutcome = Literal[
    "NOT_SUBMITTED",
    "POST_SUBMITTED",
    "POST_CONFIRMED",
    "POST_FAILED",
    "POST_OUTCOME_UNKNOWN",
    "NEEDS_HUMAN",
]


class PublishingWorkerEvent(BaseModel):
    event_id: str = Field(min_length=1)
    publish_job_id: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    occurred_at: datetime
    scene_id: str | None = None
    outcome: PublishOutcome | None = None
    correlation_id: str = Field(min_length=1)
    contract_version: str = Field(default="program3-worker-event-v1", min_length=1)


class ReconciliationEvidence(BaseModel):
    publish_job_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    externally_confirmed: bool = False
    externally_absent: bool = False
    evidence_reference: str | None = None


class ReconciliationDecision(BaseModel):
    resolved_status: Literal["CONFIRMED", "NOT_PUBLISHED", "NEEDS_HUMAN"]
    reason: str = Field(min_length=1)
