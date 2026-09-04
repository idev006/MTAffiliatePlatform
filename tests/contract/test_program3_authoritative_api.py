from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.program2_artifact import (
    InMemoryProgram2ArtifactRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_decision import (
    InMemoryProgram2DecisionRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program3_execution import (
    InMemoryProgram3ExecutionRepository,
)
from mtaffiliate.adapters.persistence.inmemory.publishing import (
    InMemoryPublishingLedgerRepository,
)
from mtaffiliate.application.program3_authority import Program3AuthoritativeService
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
    OfferSelectionDecision,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.interfaces.api.app import create_app

VIDEO_SHA = "b" * 64


def build() -> tuple[TestClient, Program3AuthoritativeService]:
    now = datetime.now(UTC)
    decisions = InMemoryProgram2DecisionRepository()
    artifacts = InMemoryProgram2ArtifactRepository()
    jobs = SharedJobEngine(InMemoryJobRepository(), token_factory=lambda: "lease-token")

    decisions.put(
        OfferSelectionDecision(
            decision_id="p2d-api-1",
            product_id="shopee:shop-1:item-1",
            affiliate_account_id="affiliate-account-1",
            source_job_id="program2-job-1",
            selected_at=now - timedelta(minutes=2),
            preferred_offer_id="offer-1",
            backup_offer_ids=("offer-2",),
            preferred_commercial_key=(
                "shopee",
                "shop-1",
                "item-1",
                "offer-1",
                "affiliate-account-1",
            ),
            evidence_refs=("offer-evidence-1",),
            feature_policy_version="features-v1",
            qualification_policy_version="qualification-v1",
            decision_policy_version="selection-v1",
            reasons=("fixture",),
        )
    )
    artifacts.put(
        AffiliateLinkArtifact(
            artifact_id="link-api-1",
            selection_decision_id="p2d-api-1",
            source_job_id="program2-job-1",
            affiliate_account_id="affiliate-account-1",
            offer_id="offer-1",
            link_url="https://example.invalid/affiliate/link-api-1",
            created_at=now - timedelta(minutes=1),
            validated_at=now - timedelta(seconds=30),
            validation_state=LinkArtifactValidationState.LAB_VALIDATED,
            evidence_refs=("link-evidence-1",),
        )
    )
    authority = Program3AuthoritativeService(
        decisions=decisions,
        artifacts=artifacts,
        execution=InMemoryProgram3ExecutionRepository(),
        ledger=InMemoryPublishingLedgerRepository(),
        jobs=jobs,
        guard=PublishingGuardEngine(),
    )
    app = create_app(
        program3_authority=authority,
        shared_jobs=jobs,
        enabled_programs={"program3"},
    )
    return TestClient(app), authority


def test_program3_authoritative_api_flow_reaches_confirmed_ledger() -> None:
    client, authority = build()
    now = datetime.now(UTC)

    registered = client.post(
        "/api/v1/workers/register",
        json={
            "worker_id": "android-worker-1",
            "worker_type": "ANDROID_PUBLISH_WORKER",
            "installation_id": "android-install-1",
            "host_id": "host-1",
            "version": "0.1.0",
            "capabilities": ["android:publish"],
        },
    )
    assert registered.status_code == 200

    plan = client.post(
        "/api/v1/program3/plans",
        json={
            "handoff": {
                "handoff_id": "p2h-api-1",
                "selection_decision_id": "p2d-api-1",
                "affiliate_account_id": "affiliate-account-1",
                "product_id": "shopee:shop-1:item-1",
                "preferred_offer_id": "offer-1",
                "backup_offer_ids": ["offer-2"],
                "link_artifact_id": "link-api-1",
                "valid_at": now.isoformat(),
                "evidence_refs": ["offer-evidence-1", "link-evidence-1"],
            },
            "plan_ref": "program3-plan:api-1",
            "publish_job_id": "program3-job-api-1",
            "target_account_id": "publish-account-1",
            "video_id": "video-api-1",
            "video_sha256": VIDEO_SHA,
            "created_at": now.isoformat(),
            "caption": "fixture",
            "tags": ["#fixture"],
        },
    )
    assert plan.status_code == 200
    assert plan.json()["source_selection_decision_id"] == "p2d-api-1"

    created = client.post(
        "/api/v1/program3/plans/program3-plan:api-1/job",
        json={
            "idempotency_key": "program3:video-api-1:publish-account-1",
            "created_at": now.isoformat(),
        },
    )
    assert created.status_code == 200
    assert created.json()["state"] == "QUEUED"

    lease = client.post(
        "/api/v1/jobs/program3-job-api-1/lease",
        json={"worker_id": "android-worker-1"},
    )
    assert lease.status_code == 200
    token = lease.json()["lease_token"]

    started = client.post(
        "/api/v1/jobs/program3-job-api-1/start",
        json={"worker_id": "android-worker-1", "lease_token": token},
    )
    assert started.status_code == 200

    pre = client.post(
        "/api/v1/program3/jobs/program3-job-api-1/pre-submit",
        json={
            "worker_id": "android-worker-1",
            "lease_token": token,
            "device_id": "device-1",
            "target_account_id": "publish-account-1",
            "scene_ready": True,
            "evaluated_at": datetime.now(UTC).isoformat(),
            "evidence_refs": ["scene-ready-api-1"],
        },
    )
    assert pre.status_code == 200
    assert pre.json()["state"] == "ALLOW_SUBMIT"

    submitted = client.post(
        "/api/v1/program3/submissions",
        json={
            "decision": pre.json(),
            "submitted_at": datetime.now(UTC).isoformat(),
            "idempotency_key": "submit-api-1",
            "evidence_refs": ["submit-evidence-api-1"],
        },
    )
    assert submitted.status_code == 200
    submission_id = submitted.json()["submission_id"]

    unknown = client.post(
        f"/api/v1/program3/submissions/{submission_id}/reconcile",
        json={"evaluated_at": datetime.now(UTC).isoformat()},
    )
    assert unknown.status_code == 200
    assert unknown.json()["outcome"] == "OUTCOME_UNKNOWN"
    assert unknown.json()["retry_allowed"] is False

    success = client.post(
        f"/api/v1/program3/submissions/{submission_id}/reconcile",
        json={
            "evaluated_at": datetime.now(UTC).isoformat(),
            "success_confirmed": True,
            "evidence_refs": ["publish-success-api-1"],
        },
    )
    assert success.status_code == 200

    confirmed = client.post(
        "/api/v1/program3/publish/confirm",
        json={
            "reconciliation": success.json(),
            "confirmed_at": datetime.now(UTC).isoformat(),
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    assert authority.ledger.history_for_video("video-api-1")[-1].status == "CONFIRMED"


def test_program3_api_blocks_unconfirmed_scene_and_unknown_retry() -> None:
    client, _authority = build()
    now = datetime.now(UTC)

    client.post(
        "/api/v1/workers/register",
        json={
            "worker_id": "android-worker-1",
            "worker_type": "ANDROID_PUBLISH_WORKER",
            "installation_id": "android-install-1",
            "version": "0.1.0",
            "capabilities": ["android:publish"],
        },
    )
    client.post(
        "/api/v1/program3/plans",
        json={
            "handoff": {
                "handoff_id": "p2h-api-1",
                "selection_decision_id": "p2d-api-1",
                "affiliate_account_id": "affiliate-account-1",
                "product_id": "shopee:shop-1:item-1",
                "preferred_offer_id": "offer-1",
                "backup_offer_ids": ["offer-2"],
                "link_artifact_id": "link-api-1",
                "valid_at": now.isoformat(),
                "evidence_refs": [],
            },
            "plan_ref": "program3-plan:api-1",
            "publish_job_id": "program3-job-api-1",
            "target_account_id": "publish-account-1",
            "video_id": "video-api-1",
            "video_sha256": VIDEO_SHA,
            "created_at": now.isoformat(),
        },
    )
    client.post(
        "/api/v1/program3/plans/program3-plan:api-1/job",
        json={"idempotency_key": "p3-idem", "created_at": now.isoformat()},
    )
    lease = client.post(
        "/api/v1/jobs/program3-job-api-1/lease",
        json={"worker_id": "android-worker-1"},
    ).json()
    client.post(
        "/api/v1/jobs/program3-job-api-1/start",
        json={"worker_id": "android-worker-1", "lease_token": lease["lease_token"]},
    )

    pre = client.post(
        "/api/v1/program3/jobs/program3-job-api-1/pre-submit",
        json={
            "worker_id": "android-worker-1",
            "lease_token": lease["lease_token"],
            "device_id": "device-1",
            "target_account_id": "publish-account-1",
            "scene_ready": False,
            "evaluated_at": datetime.now(UTC).isoformat(),
        },
    )
    assert pre.status_code == 200
    assert pre.json()["state"] == "NEEDS_HUMAN"

    attempted = client.post(
        "/api/v1/program3/submissions",
        json={
            "decision": pre.json(),
            "submitted_at": datetime.now(UTC).isoformat(),
            "idempotency_key": "forbidden-submit",
        },
    )
    assert attempted.status_code == 409
