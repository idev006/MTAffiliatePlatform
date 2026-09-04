from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
    InMemoryWorkerRegistryRepository,
)
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.domain.worker_registry.models import WorkerRegistration, WorkerType
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.interfaces.api.shared_jobs import build_shared_job_router

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.value = NOW

    def __call__(self):
        current = self.value
        self.value += timedelta(seconds=1)
        return current


def client() -> TestClient:
    repo = InMemoryJobRepository()
    engine = SharedJobEngine(repo, token_factory=lambda: "lease-1")
    program1 = Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        InMemoryProgram1StrategyRepository(),
        engine,
    )
    clock = FakeClock()
    registry = WorkerRegistryService(
        InMemoryWorkerRegistryRepository(),
        stale_after=timedelta(minutes=5),
    )
    registry.register(
        WorkerRegistration(
            worker_id="worker-1",
            worker_type=WorkerType.DISCOVERY_BROWSER_WORKER,
            installation_id="install-1",
            version="0.1.22",
            capabilities=["collector:search-lab"],
        ),
        seen_at=NOW,
    )
    app = FastAPI()
    app.include_router(
        build_shared_job_router(
            program1_jobs=program1,
            jobs=engine,
            registry=registry,
            lease_seconds=120,
            clock=clock,
        )
    )
    return TestClient(app)


def create_payload() -> dict[str, object]:
    return {
        "job_id": "job-1",
        "idempotency_key": "campaign-1:plan-1",
        "discovery_plan_ref": "program1-plan:plan-1:v1",
        "hypothesis": {
            "hypothesis_id": "hyp-1",
            "campaign_id": "campaign-1",
            "objective": "Find products worth testing",
            "decision_question": "Which products deserve affiliate effort now?",
            "rationale": "Concentrate content effort",
            "target_outcome": "candidate_hit_rate",
            "policy_version": "affiliate-strategy-v1",
            "created_at": NOW.isoformat(),
        },
        "signals": [
            {
                "signal_id": "demand",
                "hypothesis_id": "hyp-1",
                "decision_supported": "Which products deserve affiliate effort now?",
                "expected_interpretation": "demand supports priority",
                "evidence_source": "approved product observations",
            }
        ],
        "discovery_plan": {
            "plan_id": "plan-1",
            "campaign_id": "campaign-1",
            "hypothesis_id": "hyp-1",
            "required_signal_ids": ["demand"],
            "source_scope": "shopee",
            "surface_scope": ["search"],
            "capability_requirements": ["collector:search-lab"],
            "evidence_policy_version": "evidence-v1",
            "collection_policy_version": "collection-v1",
            "created_at": NOW.isoformat(),
        },
    }


def test_full_api_lifecycle_without_ui() -> None:
    c = client()
    created = c.post("/api/v1/program1/discovery-jobs", json=create_payload())
    assert created.status_code == 200
    assert created.json()["state"] == "QUEUED"

    leased = c.post(
        "/api/v1/jobs/job-1/lease",
        json={"worker_id": "worker-1"},
    )
    assert leased.status_code == 200
    assert leased.json()["state"] == "LEASED"
    token = leased.json()["lease_token"]

    started = c.post(
        "/api/v1/jobs/job-1/start",
        json={"worker_id": "worker-1", "lease_token": token},
    )
    assert started.status_code == 200
    assert started.json()["state"] == "IN_PROGRESS"

    checkpoint = c.post(
        "/api/v1/jobs/job-1/checkpoint",
        json={
            "worker_id": "worker-1",
            "lease_token": token,
            "checkpoint_type": "PAGE",
            "payload": {"page": 1},
        },
    )
    assert checkpoint.status_code == 200
    assert checkpoint.json()["checkpoint"]["payload"] == {"page": 1}

    verifying = c.post(
        "/api/v1/jobs/job-1/verify",
        json={"worker_id": "worker-1", "lease_token": token},
    )
    assert verifying.status_code == 200
    assert verifying.json()["state"] == "VERIFYING"

    completed = c.post(
        "/api/v1/jobs/job-1/complete",
        json={"worker_id": "worker-1", "lease_token": token},
    )
    assert completed.status_code == 200
    assert completed.json()["state"] == "COMPLETED"


def test_pause_resume_requires_new_lease() -> None:
    c = client()
    assert c.post("/api/v1/program1/discovery-jobs", json=create_payload()).status_code == 200
    leased = c.post(
        "/api/v1/jobs/job-1/lease",
        json={"worker_id": "worker-1"},
    ).json()
    token = leased["lease_token"]
    assert c.post(
        "/api/v1/jobs/job-1/start",
        json={"worker_id": "worker-1", "lease_token": token},
    ).status_code == 200

    paused = c.post("/api/v1/jobs/job-1/pause")
    assert paused.status_code == 200
    assert paused.json()["state"] == "PAUSED"

    stale = c.post(
        "/api/v1/jobs/job-1/checkpoint",
        json={
            "worker_id": "worker-1",
            "lease_token": token,
            "checkpoint_type": "PAGE",
            "payload": {},
        },
    )
    assert stale.status_code == 409

    resumed = c.post("/api/v1/jobs/job-1/resume")
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "QUEUED"


def test_incompatible_worker_cannot_lease_job() -> None:
    c = client()
    incompatible_payload = create_payload()
    incompatible_payload["job_id"] = "job-2"
    incompatible_payload["idempotency_key"] = "campaign-1:plan-2"
    incompatible_payload["discovery_plan_ref"] = "program1-plan:plan-2:v1"
    incompatible_payload["discovery_plan"]["plan_id"] = "plan-2"
    incompatible_payload["discovery_plan"]["capability_requirements"] = [
        "collector:shop-lab"
    ]
    assert c.post(
        "/api/v1/program1/discovery-jobs", json=incompatible_payload
    ).status_code == 200
    denied = c.post("/api/v1/jobs/job-2/lease", json={"worker_id": "worker-1"})
    assert denied.status_code == 409
    assert "lacks required capabilities" in denied.json()["detail"]


def test_undeclared_signal_is_rejected_before_job_creation() -> None:
    c = client()
    payload = create_payload()
    payload["signals"].append(
        {
            "signal_id": "rating",
            "hypothesis_id": "hyp-1",
            "decision_supported": "Which products deserve affiliate effort now?",
            "expected_interpretation": "rating may support confidence",
            "evidence_source": "page",
        }
    )

    response = c.post("/api/v1/program1/discovery-jobs", json=payload)
    assert response.status_code == 422
    assert c.get("/api/v1/jobs/job-1").status_code == 404


def test_lease_next_uses_registry_capabilities_and_priority() -> None:
    c = client()

    low = create_payload()
    low["job_id"] = "job-low"
    low["idempotency_key"] = "idem-low"
    low["discovery_plan_ref"] = "program1-plan:low:v1"
    low["priority"] = 1
    low["discovery_plan"]["plan_id"] = "plan-low"

    high = create_payload()
    high["job_id"] = "job-high"
    high["idempotency_key"] = "idem-high"
    high["discovery_plan_ref"] = "program1-plan:high:v1"
    high["priority"] = 10
    high["discovery_plan"]["plan_id"] = "plan-high"

    assert c.post("/api/v1/program1/discovery-jobs", json=low).status_code == 200
    assert c.post("/api/v1/program1/discovery-jobs", json=high).status_code == 200

    leased = c.post("/api/v1/jobs/lease-next", json={"worker_id": "worker-1"})
    assert leased.status_code == 200
    assert leased.json()["job_id"] == "job-high"


def test_unregistered_worker_cannot_lease() -> None:
    c = client()
    c.post("/api/v1/program1/discovery-jobs", json=create_payload())

    response = c.post("/api/v1/jobs/job-1/lease", json={"worker_id": "unknown"})
    assert response.status_code == 404


def test_lease_next_returns_null_when_no_compatible_job_exists() -> None:
    c = client()
    payload = create_payload()
    payload["discovery_plan"]["capability_requirements"] = ["collector:other"]
    assert c.post("/api/v1/program1/discovery-jobs", json=payload).status_code == 200

    response = c.post("/api/v1/jobs/lease-next", json={"worker_id": "worker-1"})
    assert response.status_code == 200
    assert response.json() is None


def test_renew_endpoint_extends_active_lease() -> None:
    c = client()
    assert c.post("/api/v1/program1/discovery-jobs", json=create_payload()).status_code == 200
    leased = c.post(
        "/api/v1/jobs/job-1/lease",
        json={"worker_id": "worker-1"},
    )
    assert leased.status_code == 200
    before = leased.json()["lease_until"]
    token = leased.json()["lease_token"]

    renewed = c.post(
        "/api/v1/jobs/job-1/renew",
        json={"worker_id": "worker-1", "lease_token": token},
    )
    assert renewed.status_code == 200
    assert renewed.json()["lease_until"] > before


def test_invalid_pause_and_unknown_job_paths_return_contract_errors() -> None:
    c = client()

    unknown = c.post("/api/v1/jobs/missing/pause")
    assert unknown.status_code == 404

    assert c.post("/api/v1/program1/discovery-jobs", json=create_payload()).status_code == 200
    invalid = c.post("/api/v1/jobs/job-1/pause")
    assert invalid.status_code == 409


def test_bad_worker_state_blocks_new_lease() -> None:
    c = client()
    assert c.post("/api/v1/program1/discovery-jobs", json=create_payload()).status_code == 200
    heartbeat = c.post(
        "/api/v1/workers/worker-1/heartbeat",
        json={"health_state": "DEGRADED"},
    )
    assert heartbeat.status_code == 200

    blocked = c.post("/api/v1/jobs/job-1/lease", json={"worker_id": "worker-1"})
    assert blocked.status_code == 409
    assert "not eligible for a new lease" in blocked.json()["detail"]
