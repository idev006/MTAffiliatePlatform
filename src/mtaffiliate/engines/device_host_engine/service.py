from __future__ import annotations

from datetime import datetime

from mtaffiliate.domain.device.models import DeviceAdmissionDecision, DeviceRecord


class DeviceHostEngine:
    """Pure admission rules for one-active-worker-per-device ownership."""

    def can_assign(
        self,
        device: DeviceRecord,
        *,
        worker_id: str,
        now: datetime,
    ) -> DeviceAdmissionDecision:
        if device.status == "UNAUTHORIZED":
            return DeviceAdmissionDecision(allowed=False, reason="ADB_UNAUTHORIZED_NEEDS_HUMAN")
        if device.status != "ONLINE":
            return DeviceAdmissionDecision(allowed=False, reason="DEVICE_NOT_ONLINE")
        if device.worker_id is None:
            return DeviceAdmissionDecision(allowed=True, reason="DEVICE_AVAILABLE")
        if device.worker_id == worker_id:
            return DeviceAdmissionDecision(allowed=True, reason="WORKER_ALREADY_OWNS_DEVICE")
        if device.lease_expires_at is not None and device.lease_expires_at <= now:
            return DeviceAdmissionDecision(allowed=True, reason="EXPIRED_LEASE_REASSIGNABLE")
        return DeviceAdmissionDecision(allowed=False, reason="DEVICE_OWNED_BY_ACTIVE_WORKER")
