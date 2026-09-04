from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from mtaffiliate.interfaces.api.app import create_app

NOW = datetime.now(UTC)
PRODUCT_ID = "shopee:shop-1:item-1"
VIDEO_SHA = "e" * 64


def register_worker(
    client: TestClient,
    *,
    worker_id: str,
    worker_type: str,
    installation_id: str,
    capabilities: list[str],
) -> None:
    response = client.post(
        "/api/v1/workers/register",
        json={
            "worker_id": worker_id,
            "worker_type": worker_type,
            "installation_id": installation_id,
            "version": "0.1.0",
            "capabilities": capabilities,
        },
    )
    assert response.status_code == 200


def test_program1_to_program2_to_program3_authoritative_closed_loop() -> None:
    client = TestClient(create_app(enabled_programs={"program1", "program2", "program3"}))

    # Program 1: strategy -> discovery job -> observation -> qualified handoff.
    register_worker(
        client,
        worker_id="discovery-worker",
        worker_type="DISCOVERY_BROWSER_WORKER",
        installation_id="discovery-install",
        capabilities=["collector:search-lab"],
    )
    created_p1 = client.post(
        "/api/v1/program1/discovery-jobs",
        json={
            "job_id": "program1-job-e2e",
            "idempotency_key": "campaign-e2e:plan-e2e",
            "discovery_plan_ref": "program1-plan:e2e:v1",
            "hypothesis": {
                "hypothesis_id": "hyp-e2e",
                "campaign_id": "campaign-e2e",
                "objective": "Find products worth an affiliate test",
                "decision_question": "Which product deserves controlled affiliate effort?",
                "rationale": "Allocate content effort using observed evidence",
                "target_outcome": "qualified_test_candidate",
                "audience_context": "synthetic fixture audience",
                "policy_version": "affiliate-strategy-v1",
                "created_at": NOW.isoformat(),
            },
            "signals": [
                {
                    "signal_id": "demand",
                    "hypothesis_id": "hyp-e2e",
                    "decision_supported": "Which product deserves controlled affiliate effort?",
                    "expected_interpretation": "demand and buyer-confidence support testing",
                    "evidence_source": "approved product observations",
                }
            ],
            "discovery_plan": {
                "plan_id": "plan-e2e",
                "campaign_id": "campaign-e2e",
                "hypothesis_id": "hyp-e2e",
                "required_signal_ids": ["demand"],
                "source_scope": "shopee",
                "surface_scope": ["search"],
                "capability_requirements": ["collector:search-lab"],
                "evidence_policy_version": "evidence-v1",
                "collection_policy_version": "collection-v1",
                "created_at": NOW.isoformat(),
            },
        },
    )
    assert created_p1.status_code == 200

    p1_lease = client.post(
        "/api/v1/jobs/program1-job-e2e/lease",
        json={"worker_id": "discovery-worker"},
    )
    assert p1_lease.status_code == 200
    p1_token = p1_lease.json()["lease_token"]
    assert client.post(
        "/api/v1/jobs/program1-job-e2e/start",
        json={"worker_id": "discovery-worker", "lease_token": p1_token},
    ).status_code == 200

    product_ingest = client.post(
        "/api/v1/program1/observations",
        json={
            "batch_id": "p1-batch-e2e",
            "job_id": "program1-job-e2e",
            "worker_id": "discovery-worker",
            "lease_token": p1_token,
            "observations": [
                {
                    "observation_id": "product-obs-e2e",
                    "platform": "shopee",
                    "shop_id": "shop-1",
                    "item_id": "item-1",
                    "collected_at": NOW.isoformat(),
                    "product_name": "Synthetic SSD",
                    "product_url": "https://example.invalid/product",
                    "price_current": "1590",
                    "sold_signal": 300,
                    "rating": 4.8,
                    "review_count": 120,
                    "source_worker_id": "discovery-worker",
                    "source_job_id": "program1-job-e2e",
                    "source_query": "ssd",
                    "extractor_version": "fixture-profile-v1",
                }
            ],
        },
    )
    assert product_ingest.status_code == 200

    p1_decisions = client.post(
        "/api/v1/program1/opportunities/evaluate",
        json={
            "campaign_id": "campaign-e2e",
            "evaluated_at": (NOW + timedelta(minutes=1)).isoformat(),
        },
    )
    assert p1_decisions.status_code == 200
    assert p1_decisions.json()[0]["thesis"]["recommended_action"] == "TEST_NOW"

    p1_handoffs = client.get(
        "/api/v1/program1/campaigns/campaign-e2e/qualified-handoffs"
    )
    assert p1_handoffs.status_code == 200
    p1_handoff = p1_handoffs.json()[0]
    assert p1_handoff["product_key"] == ["shopee", "shop-1", "item-1"]

    # Program 2: qualified product -> account-bound offer evidence -> decision/link -> handoff.
    register_worker(
        client,
        worker_id="offer-worker",
        worker_type="AFFILIATE_BROWSER_WORKER",
        installation_id="offer-install",
        capabilities=["offer:candidate-read"],
    )
    created_p2 = client.post(
        "/api/v1/program2/offer-discovery-jobs",
        json={
            "job_id": "program2-job-e2e",
            "idempotency_key": "campaign-e2e:offer-discovery",
            "work_ref": "program2-work:e2e:v1",
            "handoff": p1_handoff,
            "discovery_plan": {
                "plan_id": "program2-plan-e2e",
                "campaign_id": "campaign-e2e",
                "hypothesis_id": "hyp-e2e",
                "source_program1_decision_id": p1_handoff["decision_id"],
                "product_key": p1_handoff["product_key"],
                "product_name": p1_handoff["product_name"],
                "affiliate_account_id": "affiliate-account-e2e",
                "collection_targets": ["https://example.invalid/affiliate/search"],
                "capability_requirements": ["offer:candidate-read"],
                "evidence_policy_version": "p2-evidence-v1",
                "collection_policy_version": "p2-collection-v1",
                "created_at": NOW.isoformat(),
            },
        },
    )
    assert created_p2.status_code == 200

    p2_lease = client.post(
        "/api/v1/jobs/program2-job-e2e/lease",
        json={"worker_id": "offer-worker"},
    )
    assert p2_lease.status_code == 200
    p2_token = p2_lease.json()["lease_token"]
    assert client.post(
        "/api/v1/jobs/program2-job-e2e/start",
        json={"worker_id": "offer-worker", "lease_token": p2_token},
    ).status_code == 200

    offer_ingest = client.post(
        "/api/v1/program2/observations",
        json={
            "batch_id": "p2-batch-e2e",
            "job_id": "program2-job-e2e",
            "worker_id": "offer-worker",
            "lease_token": p2_token,
            "observations": [
                {
                    "observation_id": "offer-obs-e2e-1",
                    "offer_id": "offer-e2e-1",
                    "product_id": PRODUCT_ID,
                    "platform": "shopee",
                    "shop_id": "shop-1",
                    "item_id": "item-1",
                    "affiliate_account_id": "affiliate-account-e2e",
                    "session_context_id": "session-e2e",
                    "source_worker_id": "offer-worker",
                    "source_job_id": "program2-job-e2e",
                    "extractor_version": "fixture-profile-v1",
                    "observed_at": NOW.isoformat(),
                    "product_name": "Synthetic SSD",
                    "price_current": "1590",
                    "commission_rate": 12.0,
                    "rating": 4.8,
                    "review_count": 120,
                    "sold_signal": 300,
                    "available": True,
                },
                {
                    "observation_id": "offer-obs-e2e-2",
                    "offer_id": "offer-e2e-2",
                    "product_id": PRODUCT_ID,
                    "platform": "shopee",
                    "shop_id": "shop-1",
                    "item_id": "item-1",
                    "affiliate_account_id": "affiliate-account-e2e",
                    "session_context_id": "session-e2e",
                    "source_worker_id": "offer-worker",
                    "source_job_id": "program2-job-e2e",
                    "extractor_version": "fixture-profile-v1",
                    "observed_at": NOW.isoformat(),
                    "product_name": "Synthetic SSD",
                    "price_current": "1590",
                    "commission_rate": 8.0,
                    "rating": 4.8,
                    "review_count": 120,
                    "sold_signal": 300,
                    "available": True,
                },
            ],
        },
    )
    assert offer_ingest.status_code == 200
    assert offer_ingest.json()["accepted_count"] == 2

    p2_decision = client.post(
        f"/api/v1/program2/products/{PRODUCT_ID}/selection-decisions",
        json={
            "affiliate_account_id": "affiliate-account-e2e",
            "source_job_id": "program2-job-e2e",
            "evaluated_at": (NOW + timedelta(minutes=2)).isoformat(),
        },
    )
    assert p2_decision.status_code == 200
    p2_decision_body = p2_decision.json()
    assert p2_decision_body["preferred_offer_id"] == "offer-e2e-1"

    artifact = client.post(
        "/api/v1/program2/link-artifacts",
        json={
            "artifact_id": "link-e2e",
            "selection_decision_id": p2_decision_body["decision_id"],
            "source_job_id": "program2-job-e2e",
            "affiliate_account_id": "affiliate-account-e2e",
            "offer_id": "offer-e2e-1",
            "link_url": "https://example.invalid/affiliate/e2e",
            "created_at": (NOW + timedelta(minutes=2)).isoformat(),
            "validated_at": (NOW + timedelta(minutes=3)).isoformat(),
            "validation_state": "LAB_VALIDATED",
            "evidence_refs": ["link-validation-e2e"],
        },
    )
    assert artifact.status_code == 200

    p3_handoff_response = client.post(
        f"/api/v1/program2/selection-decisions/{p2_decision_body['decision_id']}/program3-handoff",
        json={"as_of": (NOW + timedelta(minutes=4)).isoformat()},
    )
    assert p3_handoff_response.status_code == 200
    p3_handoff = p3_handoff_response.json()

    # Program 3: validated commercial handoff -> device/job authority -> irreversible boundary -> ledger.
    register_worker(
        client,
        worker_id="android-worker",
        worker_type="ANDROID_PUBLISH_WORKER",
        installation_id="android-install",
        capabilities=["android:publish"],
    )
    assert client.post(
        "/api/v1/program3/devices/register",
        json={
            "device_id": "device-e2e",
            "adb_serial": "adb-device-e2e",
            "host_id": "host-e2e",
            "status": "ONLINE",
        },
    ).status_code == 200
    assert client.post(
        "/api/v1/program3/devices/device-e2e/claim",
        json={
            "worker_id": "android-worker",
            "at": (NOW + timedelta(minutes=4)).isoformat(),
        },
    ).status_code == 200

    p3_plan = client.post(
        "/api/v1/program3/plans",
        json={
            "handoff": p3_handoff,
            "plan_ref": "program3-plan:e2e",
            "publish_job_id": "program3-job-e2e",
            "target_account_id": "publish-account-e2e",
            "video_id": "video-e2e",
            "video_sha256": VIDEO_SHA,
            "created_at": (NOW + timedelta(minutes=4)).isoformat(),
            "caption": "Synthetic closed-loop fixture",
            "tags": ["#fixture"],
        },
    )
    assert p3_plan.status_code == 200

    created_p3 = client.post(
        "/api/v1/program3/plans/program3-plan:e2e/job",
        json={
            "idempotency_key": "program3:e2e",
            "created_at": (NOW + timedelta(minutes=4)).isoformat(),
        },
    )
    assert created_p3.status_code == 200

    p3_lease = client.post(
        "/api/v1/jobs/program3-job-e2e/lease",
        json={"worker_id": "android-worker"},
    )
    assert p3_lease.status_code == 200
    p3_token = p3_lease.json()["lease_token"]
    assert client.post(
        "/api/v1/jobs/program3-job-e2e/start",
        json={"worker_id": "android-worker", "lease_token": p3_token},
    ).status_code == 200

    pre_submit = client.post(
        "/api/v1/program3/jobs/program3-job-e2e/pre-submit",
        json={
            "worker_id": "android-worker",
            "lease_token": p3_token,
            "device_id": "device-e2e",
            "target_account_id": "publish-account-e2e",
            "scene_ready": True,
            "evaluated_at": (NOW + timedelta(minutes=4, seconds=10)).isoformat(),
            "evidence_refs": ["ready-scene-e2e"],
        },
    )
    assert pre_submit.status_code == 200
    assert pre_submit.json()["state"] == "ALLOW_SUBMIT"

    submitted = client.post(
        "/api/v1/program3/submissions",
        json={
            "decision_id": pre_submit.json()["decision_id"],
            "lease_token": p3_token,
            "submitted_at": (NOW + timedelta(minutes=4, seconds=11)).isoformat(),
            "idempotency_key": "submit-e2e",
            "evidence_refs": ["submit-evidence-e2e"],
        },
    )
    assert submitted.status_code == 200

    reconciled = client.post(
        f"/api/v1/program3/submissions/{submitted.json()['submission_id']}/reconcile",
        json={
            "evaluated_at": (NOW + timedelta(minutes=5)).isoformat(),
            "success_confirmed": True,
            "evidence_refs": ["publish-success-e2e"],
        },
    )
    assert reconciled.status_code == 200

    confirmed = client.post(
        "/api/v1/program3/publish/confirm",
        json={
            "reconciliation": reconciled.json(),
            "confirmed_at": (NOW + timedelta(minutes=5)).isoformat(),
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    assert confirmed.json()["video_id"] == "video-e2e"
