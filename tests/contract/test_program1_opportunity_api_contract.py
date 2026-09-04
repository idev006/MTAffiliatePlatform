from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from mtaffiliate.interfaces.api.app import create_app

NOW = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)


def client() -> TestClient:
    return TestClient(create_app(enabled_programs={"program1"}))


def discovery_payload() -> dict[str, object]:
    return {
        "job_id": "job-1",
        "idempotency_key": "campaign-1:plan-1",
        "discovery_plan_ref": "program1-plan:plan-1:v1",
        "hypothesis": {
            "hypothesis_id": "hyp-1",
            "campaign_id": "campaign-1",
            "objective": "Find controlled affiliate tests",
            "decision_question": "Which products deserve affiliate effort now?",
            "rationale": "Reduce wasted content effort",
            "target_outcome": "candidate_hit_rate",
            "audience_context": "Thai gadget buyers",
            "policy_version": "affiliate-strategy-v1",
            "created_at": NOW.isoformat(),
        },
        "signals": [
            {
                "signal_id": "demand",
                "hypothesis_id": "hyp-1",
                "decision_supported": "Which products deserve affiliate effort now?",
                "expected_interpretation": "demand supports controlled-test readiness",
                "evidence_source": "approved observations",
            }
        ],
        "discovery_plan": {
            "plan_id": "plan-1",
            "campaign_id": "campaign-1",
            "hypothesis_id": "hyp-1",
            "required_signal_ids": ["demand"],
            "source_scope": "synthetic",
            "surface_scope": ["search"],
            "collection_targets": ["https://example.invalid/search?q=ssd"],
            "capability_requirements": ["collector:search-lab"],
            "evidence_policy_version": "evidence-v1",
            "collection_policy_version": "collection-v1",
            "created_at": NOW.isoformat(),
        },
    }


def register_and_start(c: TestClient) -> str:
    registration = c.post(
        "/api/v1/workers/register",
        json={
            "schema_version": "worker-registration-v1",
            "worker_id": "worker-1",
            "worker_type": "DISCOVERY_BROWSER_WORKER",
            "installation_id": "install-1",
            "version": "0.1.24",
            "capabilities": ["collector:search-lab"],
        },
    )
    assert registration.status_code == 200
    assert c.post(
        "/api/v1/program1/discovery-jobs",
        json=discovery_payload(),
    ).status_code == 200
    leased = c.post(
        "/api/v1/jobs/job-1/lease",
        json={"worker_id": "worker-1"},
    )
    assert leased.status_code == 200
    token = leased.json()["lease_token"]
    started = c.post(
        "/api/v1/jobs/job-1/start",
        json={"worker_id": "worker-1", "lease_token": token},
    )
    assert started.status_code == 200
    return token


def observation(
    observation_id: str,
    *,
    collected_at: datetime,
    sold: int,
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "platform": "shopee",
        "shop_id": "shop-1",
        "item_id": "item-1",
        "collected_at": collected_at.isoformat(),
        "product_name": "Synthetic SSD",
        "price_current": "1590",
        "sold_signal": sold,
        "rating": 4.8,
        "review_count": 120,
        "source_worker_id": "worker-1",
        "source_job_id": "job-1",
    }


def test_job_bound_observations_produce_traceable_opportunity_and_handoff() -> None:
    c = client()
    token = register_and_start(c)

    batch = c.post(
        "/api/v1/program1/observations",
        json={
            "batch_id": "batch-1",
            "job_id": "job-1",
            "worker_id": "worker-1",
            "lease_token": token,
            "observations": [
                observation(
                    "obs-1",
                    collected_at=NOW - timedelta(days=1),
                    sold=80,
                ),
                observation("obs-2", collected_at=NOW, sold=120),
            ],
        },
    )
    assert batch.status_code == 200
    assert batch.json()["accepted_count"] == 2

    evaluated = c.post(
        "/api/v1/program1/opportunities/evaluate",
        json={
            "campaign_id": "campaign-1",
            "evaluated_at": NOW.isoformat(),
        },
    )
    assert evaluated.status_code == 200
    body = evaluated.json()
    assert len(body) == 1
    assert body[0]["source_job_id"] == "job-1"
    assert body[0]["thesis"]["recommended_action"] == "TEST_NOW"
    assert body[0]["thesis"]["target_buyer_context"] == "Thai gadget buyers"

    handoffs = c.get(
        "/api/v1/program1/campaigns/campaign-1/qualified-handoffs"
    )
    assert handoffs.status_code == 200
    assert len(handoffs.json()) == 1
    assert handoffs.json()[0]["decision_id"] == body[0]["decision_id"]


def test_job_bound_observation_without_execution_envelope_is_rejected() -> None:
    c = client()
    register_and_start(c)

    response = c.post(
        "/api/v1/program1/observations",
        json={
            "batch_id": "batch-1",
            "observations": [observation("obs-1", collected_at=NOW, sold=120)],
        },
    )
    assert response.status_code == 422
    assert "require job_id" in response.json()["detail"]


def test_forged_worker_provenance_is_rejected_before_ingest() -> None:
    c = client()
    token = register_and_start(c)
    forged = observation("obs-1", collected_at=NOW, sold=120)
    forged["source_worker_id"] = "worker-other"

    response = c.post(
        "/api/v1/program1/observations",
        json={
            "batch_id": "batch-1",
            "job_id": "job-1",
            "worker_id": "worker-1",
            "lease_token": token,
            "observations": [forged],
        },
    )
    assert response.status_code == 409
    assert "provenance" in response.json()["detail"]


def test_wrong_lease_token_is_rejected_before_ingest() -> None:
    c = client()
    register_and_start(c)

    response = c.post(
        "/api/v1/program1/observations",
        json={
            "batch_id": "batch-1",
            "job_id": "job-1",
            "worker_id": "worker-1",
            "lease_token": "wrong",
            "observations": [observation("obs-1", collected_at=NOW, sold=120)],
        },
    )
    assert response.status_code == 409

    evaluated = c.post(
        "/api/v1/program1/opportunities/evaluate",
        json={
            "campaign_id": "campaign-1",
            "evaluated_at": NOW.isoformat(),
        },
    )
    assert evaluated.status_code == 200
    assert evaluated.json() == []
