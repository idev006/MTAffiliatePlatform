from datetime import UTC, datetime, timedelta

from mtaffiliate.adapters.android.scripted import ScriptedAndroidAdapter
from mtaffiliate.adapters.persistence.inmemory.device import InMemoryDeviceRepository
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
from mtaffiliate.application.program3_device import Program3DeviceService
from mtaffiliate.application.program3_worker import Program3WorkerExecutor
from mtaffiliate.application.program3_workflow import Program3WorkflowRunner
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
    OfferSelectionDecision,
    Program3OfferHandoff,
)
from mtaffiliate.domain.publishing.models import (
    PreSubmitDecisionState,
    ReconciliationOutcome,
)
from mtaffiliate.domain.scene.models import SceneEvidence, SceneSignature
from mtaffiliate.domain.scene.workflow import SceneTransition, SceneWorkflow
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.scene_engine.service import SceneEngine
from mtaffiliate.engines.scene_engine.workflow import SceneWorkflowEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

NOW = datetime(2026, 9, 5, 1, 0, tzinfo=UTC)
PACKAGE = "com.shopee.synthetic"
VIDEO_SHA = "d" * 64


def signature(scene: str) -> SceneSignature:
    return SceneSignature(
        scene_id=scene,
        expected_package=PACKAGE,
        required_resource_ids={f"scene:{scene}"},
    )


def evidence(scene: str) -> SceneEvidence:
    return SceneEvidence(
        package_name=PACKAGE,
        resource_ids={f"scene:{scene}"},
    )


def authoritative_service() -> Program3AuthoritativeService:
    decisions = InMemoryProgram2DecisionRepository()
    artifacts = InMemoryProgram2ArtifactRepository()
    jobs = SharedJobEngine(InMemoryJobRepository(), token_factory=lambda: "lease-e2e")
    decisions.put(
        OfferSelectionDecision(
            decision_id="p2d-e2e",
            product_id="shopee:shop-e2e:item-e2e",
            affiliate_account_id="affiliate-account-e2e",
            source_job_id="program2-job-e2e",
            selected_at=NOW - timedelta(minutes=3),
            preferred_offer_id="offer-e2e",
            backup_offer_ids=("offer-backup",),
            preferred_commercial_key=(
                "shopee",
                "shop-e2e",
                "item-e2e",
                "offer-e2e",
                "affiliate-account-e2e",
            ),
            evidence_refs=("offer-evidence-e2e",),
            feature_policy_version="features-v1",
            qualification_policy_version="qualification-v1",
            decision_policy_version="selection-v1",
            reasons=("synthetic fixture",),
        )
    )
    artifacts.put(
        AffiliateLinkArtifact(
            artifact_id="link-e2e",
            selection_decision_id="p2d-e2e",
            source_job_id="program2-job-e2e",
            affiliate_account_id="affiliate-account-e2e",
            offer_id="offer-e2e",
            link_url="https://example.invalid/e2e",
            created_at=NOW - timedelta(minutes=2),
            validated_at=NOW - timedelta(minutes=1),
            validation_state=LinkArtifactValidationState.LAB_VALIDATED,
            evidence_refs=("link-evidence-e2e",),
        )
    )
    devices = Program3DeviceService(InMemoryDeviceRepository(), DeviceHostEngine())
    devices.register(
        device_id="device-e2e",
        adb_serial="adb-device-e2e",
        host_id="host-e2e",
        status="ONLINE",
    )
    devices.claim(
        "device-e2e",
        worker_id="android-worker-e2e",
        at=NOW,
        lease_for=timedelta(minutes=30),
    )
    return Program3AuthoritativeService(
        decisions=decisions,
        artifacts=artifacts,
        execution=InMemoryProgram3ExecutionRepository(),
        ledger=InMemoryPublishingLedgerRepository(),
        jobs=jobs,
        guard=PublishingGuardEngine(),
        devices=devices,
    )


def test_scripted_android_flow_reaches_durable_confirmed_publish() -> None:
    service = authoritative_service()
    package = service.build_publish_plan(
        handoff=Program3OfferHandoff(
            handoff_id="p2h-e2e",
            selection_decision_id="p2d-e2e",
            affiliate_account_id="affiliate-account-e2e",
            product_id="shopee:shop-e2e:item-e2e",
            preferred_offer_id="offer-e2e",
            backup_offer_ids=("offer-backup",),
            link_artifact_id="link-e2e",
            valid_at=NOW,
            evidence_refs=("offer-evidence-e2e", "link-evidence-e2e"),
        ),
        plan_ref="program3-plan:e2e",
        publish_job_id="program3-job-e2e",
        target_account_id="publish-account-e2e",
        video_id="video-e2e",
        video_sha256=VIDEO_SHA,
        created_at=NOW,
    )
    queued = service.create_publish_job(
        plan_ref=package.plan_ref,
        idempotency_key="program3:e2e",
        created_at=NOW,
    )
    leased = service.jobs.lease_job(
        queued.job_id,
        worker_id="android-worker-e2e",
        worker_capabilities={"android:publish"},
        at=NOW,
        lease_for=timedelta(minutes=30),
    )
    service.jobs.start_job(
        queued.job_id,
        worker_id="android-worker-e2e",
        lease_token=leased.lease_token,
        at=NOW,
    )

    scenes = [
        "VIDEO_SOURCE",
        "VIDEO_PREPARE",
        "PRODUCT_BASKET",
        "POST_DETAILS",
        "READY_TO_PUBLISH",
    ]
    signatures = [signature(scene) for scene in scenes]
    workflow = SceneWorkflow(
        workflow_id="synthetic-publish-v1",
        start_scene="VIDEO_SOURCE",
        terminal_scenes={"READY_TO_PUBLISH"},
        transitions=[
            SceneTransition(
                from_scene="VIDEO_SOURCE",
                to_scene="VIDEO_PREPARE",
                action_id="SELECT_VIDEO",
            ),
            SceneTransition(
                from_scene="VIDEO_PREPARE",
                to_scene="PRODUCT_BASKET",
                action_id="OPEN_BASKET",
            ),
            SceneTransition(
                from_scene="PRODUCT_BASKET",
                to_scene="POST_DETAILS",
                action_id="ATTACH_PRODUCT",
            ),
            SceneTransition(
                from_scene="POST_DETAILS",
                to_scene="READY_TO_PUBLISH",
                action_id="ENTER_DETAILS",
            ),
        ],
    )
    adapter = ScriptedAndroidAdapter(
        [
            evidence("VIDEO_SOURCE"),
            evidence("VIDEO_PREPARE"),
            evidence("VIDEO_PREPARE"),
            evidence("PRODUCT_BASKET"),
            evidence("PRODUCT_BASKET"),
            evidence("POST_DETAILS"),
            evidence("POST_DETAILS"),
            evidence("READY_TO_PUBLISH"),
        ]
    )
    runner = Program3WorkflowRunner(
        Program3WorkerExecutor(
            scene_engine=SceneEngine(),
            workflow_engine=SceneWorkflowEngine(),
            ui=adapter,
            evidence=adapter,
            checkpoints=adapter,
        )
    )
    result = runner.run(
        publish_job_id=queued.job_id,
        device_id="device-e2e",
        workflow=workflow,
        signatures=signatures,
        actions=["SELECT_VIDEO", "OPEN_BASKET", "ATTACH_PRODUCT", "ENTER_DETAILS"],
    )
    assert result.success is True
    assert result.final_scene == "READY_TO_PUBLISH"
    assert len(adapter.actions) == 4
    assert len(adapter.checkpoints) == 4

    pre = service.pre_submit(
        publish_job_id=queued.job_id,
        worker_id="android-worker-e2e",
        lease_token=leased.lease_token,
        device_id="device-e2e",
        target_account_id="publish-account-e2e",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
        evidence_refs=("ready-scene-e2e",),
    )
    assert pre.state is PreSubmitDecisionState.ALLOW_SUBMIT

    submitted = service.record_post_submitted(
        decision_id=pre.decision_id,
        lease_token=leased.lease_token,
        submitted_at=NOW + timedelta(minutes=1, seconds=1),
        idempotency_key="submit-e2e",
        evidence_refs=("submit-evidence-e2e",),
    )
    assert service.jobs.repository.get(queued.job_id).checkpoint.checkpoint_type == "POST_SUBMITTED"

    unknown = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=2),
    )
    assert unknown.outcome is ReconciliationOutcome.OUTCOME_UNKNOWN
    assert unknown.retry_allowed is False

    success = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=3),
        success_confirmed=True,
        evidence_refs=("publish-success-e2e",),
    )
    confirmed = service.confirm_success(
        reconciliation=success,
        confirmed_at=NOW + timedelta(minutes=3),
    )
    assert confirmed.status == "CONFIRMED"
    assert service.ledger.history_for_video("video-e2e")[-1] == confirmed


def test_destructive_transition_failure_requires_human_reconciliation() -> None:
    workflow = SceneWorkflow(
        workflow_id="synthetic-submit-failure-v1",
        start_scene="READY_TO_PUBLISH",
        terminal_scenes={"PUBLISH_SUCCESS"},
        transitions=[
            SceneTransition(
                from_scene="READY_TO_PUBLISH",
                to_scene="PUBLISH_SUCCESS",
                action_id="SUBMIT",
            )
        ],
    )
    adapter = ScriptedAndroidAdapter(
        [
            evidence("READY_TO_PUBLISH"),
            SceneEvidence(package_name=PACKAGE, resource_ids={"unknown"}),
        ]
    )
    executor = Program3WorkerExecutor(
        scene_engine=SceneEngine(),
        workflow_engine=SceneWorkflowEngine(),
        ui=adapter,
        evidence=adapter,
        checkpoints=adapter,
    )
    result = executor.execute_action(
        publish_job_id="job-destructive",
        device_id="device-destructive",
        workflow=workflow,
        signatures=[signature("READY_TO_PUBLISH"), signature("PUBLISH_SUCCESS")],
        action_id="SUBMIT",
        destructive_action=True,
    )
    assert result.success is False
    assert result.recovery is not None
    assert result.recovery.level == "NEEDS_HUMAN"
    assert result.recovery.reason == "POST_SUBMITTED_OUTCOME_MUST_BE_RECONCILED"
