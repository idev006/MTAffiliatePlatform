from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WorkerType(str, Enum):
    """Worker types defined by the Shared Core specification."""

    DISCOVERY_BROWSER_WORKER = "DISCOVERY_BROWSER_WORKER"
    AFFILIATE_BROWSER_WORKER = "AFFILIATE_BROWSER_WORKER"
    ANDROID_PUBLISH_WORKER = "ANDROID_PUBLISH_WORKER"


class WorkerHealthState(str, Enum):
    """Registry health states recommended by the Shared Core specification."""

    ONLINE_IDLE = "ONLINE_IDLE"
    ONLINE_BUSY = "ONLINE_BUSY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"


WORKER_REPORTABLE_HEALTH_STATES: frozenset[WorkerHealthState] = frozenset(
    {
        WorkerHealthState.ONLINE_IDLE,
        WorkerHealthState.ONLINE_BUSY,
        WorkerHealthState.DEGRADED,
    }
)


class WorkerRegistration(BaseModel):
    """Payload a worker sends when it enrolls with the Back Office registry."""

    model_config = ConfigDict(str_strip_whitespace=True)

    schema_version: str = Field(default="worker-registration-v1", min_length=1)
    worker_id: str = Field(min_length=1)
    worker_type: WorkerType
    installation_id: str = Field(min_length=1)
    host_id: str | None = Field(default=None, min_length=1)
    version: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)

    @property
    def clean_capabilities(self) -> list[str]:
        return [capability.strip() for capability in self.capabilities if capability.strip()]


class WorkerRecord(BaseModel):
    """Canonical registry row: current projection of one worker's enrollment."""

    worker_id: str = Field(min_length=1)
    worker_type: WorkerType
    installation_id: str = Field(min_length=1)
    host_id: str | None = Field(default=None, min_length=1)
    version: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    health_state: WorkerHealthState
    enrolled_at: datetime
    last_seen_at: datetime
    version_no: int = Field(ge=1)


class WorkerSummary(BaseModel):
    """Operator-facing view; health_state reflects derived OFFLINE staleness."""

    worker_id: str = Field(min_length=1)
    worker_type: WorkerType
    health_state: WorkerHealthState
    last_seen_at: datetime
    version_no: int = Field(ge=1)
    stale: bool = False
