from __future__ import annotations

from mtaffiliate.domain.device.resources import (
    HostResourcePolicy,
    HostResourceSnapshot,
    ResourceAdmissionDecision,
)


class ResourceAdmissionEngine:
    """Protect correctness by refusing new work under host pressure."""

    def evaluate(
        self,
        snapshot: HostResourceSnapshot,
        policy: HostResourcePolicy,
    ) -> ResourceAdmissionDecision:
        reasons: list[str] = []
        if snapshot.cpu_percent >= policy.max_cpu_percent:
            reasons.append("CPU_PRESSURE")
        if snapshot.memory_percent >= policy.max_memory_percent:
            reasons.append("MEMORY_PRESSURE")
        if snapshot.disk_percent >= policy.max_disk_percent:
            reasons.append("DISK_PRESSURE")
        if snapshot.active_streams >= policy.max_streams and policy.max_streams >= 0:
            reasons.append("STREAM_CAPACITY")
        if snapshot.active_workers >= policy.max_workers:
            reasons.append("WORKER_CAPACITY")
        if not reasons:
            return ResourceAdmissionDecision(allowed=True, state="HEALTHY")
        severe = any(
            reason in {"DISK_PRESSURE", "MEMORY_PRESSURE", "WORKER_CAPACITY"}
            for reason in reasons
        )
        return ResourceAdmissionDecision(
            allowed=False,
            state="THROTTLED" if severe else "PRESSURED",
            reasons=reasons,
        )
