from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from mtaffiliate.interfaces.api.app import create_app

NOW = datetime(2026, 9, 4, 18, 0, tzinfo=UTC)
PRODUCT_ID = "shopee:shop-1:item-1"


def client() -> TestClient:
    return TestClient(create_app(enabled_programs={"program2"}))


def register_worker(c: TestClient) -> None:
    response = c.post(
        "/api/v1/workers/register",
        json={
            "schema_version": "worker-registration-v1",
            "worker_id": "offer-worker-1",
            "worker_type": "AFFILIATE_OFFER_BROWSER_WORKER",
            "installation_id": "install-1",
            "version": "0.1.0",
            "capabilities": ["offer:candidate-read"],
        },
    )
    assert response.status_code == 200


def create_offer_job(c: TestClient) -> None:
    response = c.post(
        "/api/v1/program2/offer-discovery-jobs",
        json={
            "job_id": "program2-job-1",
            "idempotency_key": "campaign-1:p1d-1:account-1",
            "work_ref": "program2-work:plan-1:v1",
            "handoff": {
                "handoff_id": "p1h-p1d-1",
                "decision_id": "p1d-1",
                "campaign_id": "campaign-1",
                "hypothesis_id": "hyp-1",
                "source_job_id": "program1-job-1",
                "product_key": ["shopee", "shop-1", "item-1"],
                "product_name": "Synthetic SSD",
                "recommended_action": "TEST_NOW",
                "evidence_refs": ["product-obs-1"],
                "feature_policy_version": "p1-features-v1",
                "qualification_policy_version": "p1-qualification-v1",
            },
            "discovery_plan": {
                "plan_id": "program2-plan-1",
                "campaign_id": "campaign-1",
                "hypothesis_id": "hyp-1",
                "source_program1_decision_id": "p1d-1",
                "product_key": ["shopee", "shop-1", "item-1"],
                "product_name": "Synthetic SSD",
                "affiliate_account_id": "account-1",
                "collection_targets": ["https://example.invalid/affiliate/search"],
                "capability_requirements": ["offer:candidate-read"],
                "evidence_policy_version": "p2-evidence-v1",
                "collection_policy_version": "p2-collection-v1",
                "created_at": NOW.isoformat(),
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["state"] == "QUEUED"


def lease_and_start(c: TestClient) -> str:
    lease = c.post(
        "/api/v1/jobs/program2-job-1/lease",
        json={"worker_id": "offer-worker-1"},
    )
    assert lease.status_code == 200
    token = lease.json()["lease_token"]
    started = c.post(
        "/api/v1/jobs/program2-job-1/start",
        json={"worker_id": "offer-worker-1", "lease_token": token},
    )
    assert started.status_code == 200
    return token


def offer_observation(
    observation_id: str,
    offer_id: str,
    commission: float,
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "offer_id": offer_id,
        "product_id": PRODUCT_ID,
        "platform": "shopee",
        "shop_id": f"shop-{offer_id}",
        "item_id": "item-1",
        "affiliate_account_id": "account-1",
        "session_context_id": "session-1",
        "source_worker_id": "offer-worker-1",
        "source_job_id": "program2-job-1",
        "extractor_version": "fixture-profile-v1",
        "observed_at": NOW.isoformat(),
        "seller_name": f"Seller {offer_id}",
        "product_name": "Synthetic SSD",
        "price_current": "1590",
        "commission_rate": commission,
        "extra_commission_rate": 0,
        "rating": 4.8,
        "review_count": 120,
        "sold_signal": 300,
        "available": True,
    }


def test_authoritative_program2_flow_reaches_program3_handoff() -> None:
    c = client()
    register_worker(c)
    create_offer_job(c)
    token = lease_and_start(c)

    work = c.get(
        "/api/v1/program2/offer-discovery-jobs/program2-job-1/work-package"
    )
    assert work.status_code == 200
    assert work.json()["product_id"] == PRODUCT_ID
    assert work.json()["affiliate_account_id"] == "account-1"

    ingest = c.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "offer-batch-1",
            "job_id": "program2-job-1",
            "worker_id": "offer-worker-1",
            "lease_token": token,
            "observations": [
                offer_observation("offer-obs-1", "offer-1", 12.0),
                offer_observation("offer-obs-2", "offer-2", 8.0),
            ],
        },
    )
    assert ingest.status_code == 200
    assert ingest.json()["accepted_count"] == 2

    decision = c.post(
        f"/api/v1/program2/products/{PRODUCT_ID}/selection-decisions",
        json={
            "affiliate_account_id": "account-1",
            "source_job_id": "program2-job-1",
            "evaluated_at": NOW.isoformat(),
        },
    )
    assert decision.status_code == 200
    decision_body = decision.json()
    assert decision_body["preferred_offer_id"] == "offer-1"
    assert decision_body["backup_offer_ids"] == ["offer-2"]

    artifact = c.post(
        "/api/v1/program2/link-artifacts",
        json={
            "artifact_id": "artifact-1",
            "selection_decision_id": decision_body["decision_id"],
            "source_job_id": "program2-job-1",
            "affiliate_account_id": "account-1",
            "offer_id": "offer-1",
            "link_url": "https://example.invalid/affiliate/link-1",
            "created_at": (NOW + timedelta(minutes=1)).isoformat(),
            "validated_at": (NOW + timedelta(minutes=2)).isoformat(),
            "validation_state": "LAB_VALIDATED",
            "evidence_refs": ["export-fixture-1"],
        },
    )
    assert artifact.status_code == 200

    handoff = c.post(
        f"/api/v1/program2/selection-decisions/{decision_body['decision_id']}/program3-handoff",
        json={"as_of": (NOW + timedelta(minutes=3)).isoformat()},
    )
    assert handoff.status_code == 200
    body = handoff.json()
    assert body["preferred_offer_id"] == "offer-1"
    assert body["link_artifact_id"] == "artifact-1"
    assert set(body["evidence_refs"]) == {
        "offer-obs-1",
        "offer-obs-2",
        "export-fixture-1",
    }


def test_program2_ingest_rejects_forged_worker_or_missing_session() -> None:
    c = client()
    register_worker(c)
    create_offer_job(c)
    token = lease_and_start(c)

    forged = offer_observation("offer-obs-1", "offer-1", 12.0)
    forged["source_worker_id"] = "other-worker"
    response = c.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "offer-batch-1",
            "job_id": "program2-job-1",
            "worker_id": "offer-worker-1",
            "lease_token": token,
            "observations": [forged],
        },
    )
    assert response.status_code == 409

    missing_session = offer_observation("offer-obs-2", "offer-2", 10.0)
    missing_session["session_context_id"] = None
    response = c.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "offer-batch-2",
            "job_id": "program2-job-1",
            "worker_id": "offer-worker-1",
            "lease_token": token,
            "observations": [missing_session],
        },
    )
    assert response.status_code == 422


def test_program2_ingest_rejects_wrong_account_or_lease() -> None:
    c = client()
    register_worker(c)
    create_offer_job(c)
    token = lease_and_start(c)

    wrong_account = offer_observation("offer-obs-1", "offer-1", 12.0)
    wrong_account["affiliate_account_id"] = "other-account"
    response = c.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "offer-batch-1",
            "job_id": "program2-job-1",
            "worker_id": "offer-worker-1",
            "lease_token": token,
            "observations": [wrong_account],
        },
    )
    assert response.status_code == 409

    response = c.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "offer-batch-2",
            "job_id": "program2-job-1",
            "worker_id": "offer-worker-1",
            "lease_token": "wrong-token",
            "observations": [
                offer_observation("offer-obs-2", "offer-2", 10.0)
            ],
        },
    )
    assert response.status_code == 409
