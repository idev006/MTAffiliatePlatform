from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceRecord(BaseModel):
    device_id: str = Field(min_length=1)
    adb_serial: str = Field(min_length=1)
    host_id: str = Field(min_length=1)
    status: str = Field(pattern="^(ONLINE|OFFLINE|UNAUTHORIZED|MISSING)$")
    worker_id: str | None = None
    lease_expires_at: datetime | None = None


class DeviceAdmissionDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1)
