from __future__ import annotations

import pytest
from pydantic import ValidationError

from mtaffiliate.domain.device.resources import HostResourcePolicy, HostResourceSnapshot
from mtaffiliate.domain.publishing.events import ReconciliationEvidence
from mtaffiliate.engines.device_host_engine.resources import ResourceAdmissionEngine
from mtaffiliate.engines.publishing_guard_engine.reconciliation import (
    PublishReconciliationEngine,
)


def evidence(**updates) -> ReconciliationEvidence:
    data = {
        "publish_job_id": "job-1",
        "platform": "shopee",
        "video_id": "video-1",
    }
    data.update(updates)
    return ReconciliationEvidence(**data)


def test_reconciliation_is_conservative() -> None:
    engine = PublishReconciliationEngine()
    assert engine.reconcile(evidence(externally_confirmed=True)).resolved_status == "CONFIRMED"
    assert engine.reconcile(evidence(externally_absent=True)).resolved_status == "NOT_PUBLISHED"
    assert engine.reconcile(evidence()).resolved_status == "NEEDS_HUMAN"
    assert engine.reconcile(
        evidence(externally_confirmed=True, externally_absent=True)
    ).reason == "CONFLICTING_EXTERNAL_EVIDENCE"


def test_resource_admission_allows_healthy_and_throttles_pressure() -> None:
    engine = ResourceAdmissionEngine()
    policy = HostResourcePolicy(max_streams=10, max_workers=10)
    healthy = HostResourceSnapshot(
        cpu_percent=20,
        memory_percent=30,
        disk_percent=40,
        active_streams=1,
        active_workers=2,
    )
    assert engine.evaluate(healthy, policy).allowed

    cpu_pressure = healthy.model_copy(update={"cpu_percent": 90})
    decision = engine.evaluate(cpu_pressure, policy)
    assert not decision.allowed
    assert decision.state == "PRESSURED"
    assert "CPU_PRESSURE" in decision.reasons

    memory_pressure = healthy.model_copy(update={"memory_percent": 90})
    decision = engine.evaluate(memory_pressure, policy)
    assert not decision.allowed
    assert decision.state == "THROTTLED"


def test_resource_policy_rejects_invalid_percentages() -> None:
    with pytest.raises(ValidationError):
        HostResourceSnapshot(
            cpu_percent=101,
            memory_percent=0,
            disk_percent=0,
            active_streams=0,
            active_workers=0,
        )
