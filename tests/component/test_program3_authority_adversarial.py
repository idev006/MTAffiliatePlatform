from datetime import UTC, datetime, timedelta

import pytest

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
    Program3OfferHandoff,
)
from mtaffiliate.domain.publishing.models import (
    PreSubmitDecision,
    PreSubmitDecisionState,
    PublishingLedgerEntry,
    ReconciliationDecision,
    ReconciliationOutcome,
    SubmissionRecord,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.ports.repositories.program3_execution import Program3ExecutionConflictError

NOW = datetime(2026, 9, 4, 21, 0, tzinfo=UTC)
VIDEO_SHA = "c" * 64


def decision() -> OfferSelectionDecision:
    return OfferSelectionDecision(
        decision_id="p2d-adv",
        product_id="shopee:shop-1:item-1",
        affiliate_account_id="affiliate-account-1",
        source_job_id="program2-job-1",
        selected_at=NOW - timedelta(minutes=3),
        preferred_offer_id="offer-1",
        backup_offer_ids=("offer-2",),
        preferred_commercial_key=(
            "shopee",
            "shop-1",
            "item-1",
            "offer-1",
            "affiliate-account-1",
        ),
        evidence_refs=("offer-evidence",),
        feature_policy_version="features-v1",
        qualification_policy_version="qualification-v1",
        decision_policy_version="selection-v1",
        reasons=("fixture",),
    )


def link(
    artifact_id: str = "link-adv",
    *,
    selection_decision_id: str = "p2d-adv",
    offer_id: str = "offer-1",
    state: LinkArtifactValidationState = LinkArtifactValidationState.LAB_VALIDATED,
    validated_at: datetime | None = NOW - timedelta(seconds=30),
) -> AffiliateLinkArtifact:
    return AffiliateLinkArtifact(
        artifact_id=artifact_id,
        selection_decision_id=selection_decision_id,
        source_job_id="program2-job-1",
        affiliate_account_id="affiliate-account-1",
        offer_id=offer_id,
        link_url=f"https://example.invalid/{artifact_id}",
        created_at=NOW - timedelta(minutes=1),
        validated_at=validated_at,
        validation_state=state,
        evidence_refs=(f"evidence-{artifact_id}",),
    )


def handoff() -> Program3OfferHandoff:
    return Program3OfferHandoff(
        handoff_id="p2h-adv",
        selection_decision_id="p2d-adv",
        affiliate_account_id="affiliate-account-1",
        product_id="shopee:shop-1:item-1",
        preferred_offer_id="offer-1",
        backup_offer_ids=("offer-2",),
        link_artifact_id="link-adv",
        valid_at=NOW,
        evidence_refs=("offer-evidence", "link-evidence"),
    )


def service():
    decisions = InMemoryProgram2DecisionRepository()
    artifacts = InMemoryProgram2ArtifactRepository()
    execution = InMemoryProgram3ExecutionRepository()
    ledger = InMemoryPublishingLedgerRepository()
    jobs = SharedJobEngine(InMemoryJobRepository(), token_factory=lambda: "lease-adv")
    decisions.put(decision())
    artifacts.put(link())
    return Program3AuthoritativeService(
        decisions=decisions,
        artifacts=artifacts,
        execution=execution,
        ledger=ledger,
        jobs=jobs,
        guard=PublishingGuardEngine(),
    )


def build_plan(svc: Program3AuthoritativeService):
    return svc.build_publish_plan(
        handoff=handoff(),
        plan_ref="plan-adv",
        publish_job_id="program3-job-adv",
        target_account_id="publish-account-1",
        video_id="video-adv",
        video_sha256=VIDEO_SHA,
        created_at=NOW,
    )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda h: h.model_copy(update={"product_id": "wrong"}), "product mismatch"),
        (lambda h: h.model_copy(update={"preferred_offer_id": "wrong"}), "preferred offer mismatch"),
        (lambda h: h.model_copy(update={"affiliate_account_id": "wrong"}), "affiliate account mismatch"),
        (lambda h: h.model_copy(update={"backup_offer_ids": ("wrong",)}), "backup offer mismatch"),
        (
            lambda h: h.model_copy(update={"valid_at": NOW - timedelta(hours=7)}),
            "stale or has invalid time",
        ),
        (
            lambda h: h.model_copy(update={"valid_at": NOW + timedelta(seconds=1)}),
            "stale or has invalid time",
        ),
    ],
)
def test_program2_handoff_identity_and_freshness_are_strict(mutator, message: str) -> None:
    svc = service()
    with pytest.raises(ValueError, match=message):
        svc.build_publish_plan(
            handoff=mutator(handoff()),
            plan_ref="plan-adv",
            publish_job_id="program3-job-adv",
            target_account_id="publish-account-1",
            video_id="video-adv",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )


def test_plan_admission_rejects_missing_decision_artifact_and_blank_reference() -> None:
    svc = service()
    with pytest.raises(ValueError, match="plan_ref"):
        svc.build_publish_plan(
            handoff=handoff(),
            plan_ref=" ",
            publish_job_id="job",
            target_account_id="account",
            video_id="video",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )
    with pytest.raises(ValueError, match="selection decision does not exist"):
        svc.build_publish_plan(
            handoff=handoff().model_copy(update={"selection_decision_id": "missing"}),
            plan_ref="plan",
            publish_job_id="job",
            target_account_id="account",
            video_id="video",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )
    with pytest.raises(ValueError, match="link artifact does not exist"):
        svc.build_publish_plan(
            handoff=handoff().model_copy(update={"link_artifact_id": "missing"}),
            plan_ref="plan",
            publish_job_id="job",
            target_account_id="account",
            video_id="video",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )


def test_plan_rejects_artifact_ownership_offer_and_validation_defects() -> None:
    svc = service()
    cases = [
        (
            link("bad-selection", selection_decision_id="other"),
            "selection decision",
        ),
        (
            link("bad-offer", offer_id="other"),
            "preferred offer",
        ),
        (
            link(
                "bad-state",
                state=LinkArtifactValidationState.OUTCOME_UNKNOWN,
                validated_at=None,
            ),
            "not validated",
        ),
        (
            link("missing-validated-at", validated_at=None),
            "requires validated_at",
        ),
    ]
    for artifact, message in cases:
        svc.artifacts.put(artifact)
        with pytest.raises(ValueError, match=message):
            svc.build_publish_plan(
                handoff=handoff().model_copy(update={"link_artifact_id": artifact.artifact_id}),
                plan_ref=f"plan-{artifact.artifact_id}",
                publish_job_id=f"job-{artifact.artifact_id}",
                target_account_id="account",
                video_id=f"video-{artifact.artifact_id}",
                video_sha256=VIDEO_SHA,
                created_at=NOW,
            )


def test_publish_job_requires_plan_and_replay_is_idempotent() -> None:
    svc = service()
    with pytest.raises(ValueError, match="publish plan package is missing"):
        svc.create_publish_job(
            plan_ref="missing",
            idempotency_key="missing",
            created_at=NOW,
        )
    package = build_plan(svc)
    first = svc.create_publish_job(
        plan_ref=package.plan_ref,
        idempotency_key="p3-idem",
        created_at=NOW,
    )
    replay = svc.create_publish_job(
        plan_ref=package.plan_ref,
        idempotency_key="p3-idem",
        created_at=NOW,
    )
    assert replay.job_id == first.job_id
    assert replay.state == first.state


def test_pre_submit_rechecks_duplicate_history_after_planning() -> None:
    svc = service()
    package = build_plan(svc)
    queued = svc.create_publish_job(
        plan_ref=package.plan_ref,
        idempotency_key="p3-idem",
        created_at=NOW,
    )
    leased = svc.jobs.lease_job(
        queued.job_id,
        worker_id="worker-1",
        worker_capabilities={"android:publish"},
        at=NOW,
        lease_for=timedelta(minutes=30),
    )
    svc.jobs.start_job(
        queued.job_id,
        worker_id="worker-1",
        lease_token=leased.lease_token,
        at=NOW,
    )
    svc.ledger.append(
        PublishingLedgerEntry(
            publish_job_id="other-job",
            platform="shopee",
            target_account_id="other-account",
            video_id="video-adv",
            video_sha256=VIDEO_SHA,
            status="CONFIRMED",
            updated_at=NOW + timedelta(seconds=1),
        )
    )
    pre = svc.pre_submit(
        publish_job_id=queued.job_id,
        worker_id="worker-1",
        lease_token=leased.lease_token,
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    assert pre.state is PreSubmitDecisionState.REJECT
    assert "VIDEO_ALREADY_PUBLISHED_TO_PLATFORM" in pre.reasons


def test_submission_and_reconciliation_missing_state_fail_closed() -> None:
    svc = service()
    denied = PreSubmitDecision(
        decision_id="pre-denied",
        publish_job_id="job",
        plan_ref="plan",
        worker_id="worker",
        device_id="device",
        target_account_id="account",
        evaluated_at=NOW,
        state=PreSubmitDecisionState.REJECT,
        policy_version="p3",
    )
    svc.execution.put_pre_submit(denied)
    with pytest.raises(ValueError, match="requires ALLOW_SUBMIT"):
        svc.record_post_submitted(
            decision_id=denied.decision_id,
            lease_token="irrelevant-for-denied-decision",
            submitted_at=NOW,
            idempotency_key="submit",
        )
    with pytest.raises(ValueError, match="pre-submit decision does not exist"):
        svc.record_post_submitted(
            decision_id="forged-allow-submit",
            lease_token="forged-token",
            submitted_at=NOW,
            idempotency_key="forged-submit",
        )
    with pytest.raises(ValueError, match="submission does not exist"):
        svc.reconcile(
            submission_id="missing",
            evaluated_at=NOW,
        )


def test_confirm_success_requires_submission_plan_and_no_other_job_duplicate() -> None:
    svc = service()
    missing_submission = ReconciliationDecision(
        reconciliation_id="rec-missing",
        submission_id="missing",
        publish_job_id="job",
        evaluated_at=NOW,
        outcome=ReconciliationOutcome.CONFIRMED_SUCCESS,
        retry_allowed=False,
        policy_version="p3",
    )
    with pytest.raises(ValueError, match="submission does not exist"):
        svc.confirm_success(
            reconciliation=missing_submission,
            confirmed_at=NOW,
        )

    svc.execution.put_submission(
        SubmissionRecord(
            submission_id="sub-no-plan",
            publish_job_id="job-no-plan",
            plan_ref="missing-plan",
            worker_id="worker",
            device_id="device",
            submitted_at=NOW,
            idempotency_key="idempotency",
        )
    )
    no_plan = missing_submission.model_copy(
        update={
            "reconciliation_id": "rec-no-plan",
            "submission_id": "sub-no-plan",
            "publish_job_id": "job-no-plan",
        }
    )
    with pytest.raises(ValueError, match="publish plan package does not exist"):
        svc.confirm_success(reconciliation=no_plan, confirmed_at=NOW)

    package = build_plan(svc)
    svc.execution.put_submission(
        SubmissionRecord(
            submission_id="sub-duplicate",
            publish_job_id=package.publish_plan.publish_job_id,
            plan_ref=package.plan_ref,
            worker_id="worker",
            device_id="device",
            submitted_at=NOW,
            idempotency_key="submit-duplicate",
        )
    )
    svc.ledger.append(
        PublishingLedgerEntry(
            publish_job_id="other-job",
            platform=package.publish_plan.platform,
            target_account_id="other-account",
            video_id=package.publish_plan.video_id,
            video_sha256=package.publish_plan.video_sha256,
            status="CONFIRMED",
            updated_at=NOW,
        )
    )
    duplicate = missing_submission.model_copy(
        update={
            "reconciliation_id": "rec-duplicate",
            "submission_id": "sub-duplicate",
            "publish_job_id": package.publish_plan.publish_job_id,
        }
    )
    with pytest.raises(ValueError, match="VIDEO_ALREADY_PUBLISHED"):
        svc.confirm_success(reconciliation=duplicate, confirmed_at=NOW)


def test_inmemory_execution_repository_conflicts_and_latest_reconciliation() -> None:
    repo = InMemoryProgram3ExecutionRepository()
    svc = service()
    package = build_plan(svc)
    repo.put_plan(package)
    repo.put_plan(package)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_plan(package.model_copy(update={"evidence_refs": ("other",)}))

    submission = SubmissionRecord(
        submission_id="sub-1",
        publish_job_id="job-1",
        plan_ref="plan",
        worker_id="worker",
        device_id="device",
        submitted_at=NOW,
        idempotency_key="idem",
    )
    repo.put_submission(submission)
    repo.put_submission(submission)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_submission(submission.model_copy(update={"device_id": "other"}))
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_submission(
            submission.model_copy(
                update={
                    "submission_id": "sub-2",
                    "idempotency_key": "other",
                }
            )
        )

    rec1 = ReconciliationDecision(
        reconciliation_id="rec-1",
        submission_id="sub-1",
        publish_job_id="job-1",
        evaluated_at=NOW,
        outcome=ReconciliationOutcome.OUTCOME_UNKNOWN,
        retry_allowed=False,
        policy_version="p3",
    )
    rec2 = rec1.model_copy(
        update={
            "reconciliation_id": "rec-2",
            "evaluated_at": NOW + timedelta(seconds=1),
            "outcome": ReconciliationOutcome.NEEDS_HUMAN,
        }
    )
    repo.put_reconciliation(rec1)
    repo.put_reconciliation(rec1)
    repo.put_reconciliation(rec2)
    assert repo.latest_reconciliation("sub-1") == rec2
    assert repo.latest_reconciliation("missing") is None
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_reconciliation(rec1.model_copy(update={"retry_allowed": True}))
