from __future__ import annotations

from pydantic import BaseModel, Field


class HostResourceSnapshot(BaseModel):
    cpu_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    memory_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    disk_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    active_streams: int = Field(ge=0)
    active_workers: int = Field(ge=0)


class HostResourcePolicy(BaseModel):
    max_cpu_percent: float = Field(default=85, gt=0, le=100, allow_inf_nan=False)
    max_memory_percent: float = Field(default=85, gt=0, le=100, allow_inf_nan=False)
    max_disk_percent: float = Field(default=90, gt=0, le=100, allow_inf_nan=False)
    max_streams: int = Field(default=10, ge=0)
    max_workers: int = Field(default=10, ge=1)


class ResourceAdmissionDecision(BaseModel):
    allowed: bool
    state: str = Field(pattern="^(HEALTHY|PRESSURED|THROTTLED)$")
    reasons: list[str] = Field(default_factory=list)
