from datetime import UTC, datetime, timedelta

import pytest

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
from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.application.program3_authority import (
    Program3AuthorityPolicy,
    Program3AuthoritativeService,
)
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
    OfferSelectionDecision,
    Program3OfferHandoff,
)
from mtaffiliate.domain.publishing.models import (
    PreSubmitDecisionState,
    PublishingLedgerEntry,
    ReconciliationOutcome,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

NOW = datetime(2026, 9, 4, 19, 0, tzinfo=UTC)
VIDEO_SHA = "a" * 64


def selected() -> OfferSelectionDecision:
    return OfferSelectionDecision(
        decision_id="p2d-1",
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
        evidence_refs=("offer-obs-1",),
        feature_policy_version="features-v1",
        qualification_policy_version="qualification-v1",
        decision_policy_version="selection-v1",
        reasons=("fixture",),
    )


def artifact(
    state: LinkArtifactValidationState = LinkArtifactValidationState.LAB_VALIDATED,
) -> AffiliateLinkArtifact:
    return AffiliateLinkArtifact(
        artifact_id="link-1",
        selection_decision_id="p2d-1",
        source_job_id="program2-job-1",
        affiliate_account_id="affiliate-account-1",
        offer_id="offer-1",
        link_url="https://example.invalid/affiliate/link-1",
        created_at=NOW - timedelta(minutes=2),
        validated_at=NOW - timedelta(minutes=1),
        validation_state=state,
        evidence_refs=("link-evidence-1",),
    )


def handoff(valid_at: datetime = NOW) -> Program3OfferHandoff:
    return Program3OfferHandoff(
        handoff_id="p2h-1",
        selection_decision_id="p2d-1",
        affiliate_account_id="affiliate-account-1",
        product_id="shopee:shop-1:item-1",
        preferred_offer_id="offer-1",
        backup_offer_ids=("offer-2",),
        link_artifact_id="link-1",
        valid_at=valid_at,
        evidence_refs=("offer-obs-1", "link-evidence-1"),
    )


def build(
    *,
    handoff_age: timedelta = timedelta(hours=6),
    artifact_state: LinkArtifactValidationState = LinkArtifactValidationState.LAB_VALIDATED,
):
    decisions = InMemoryProgram2DecisionRepository()
    artifacts = InMemoryProgram2ArtifactRepository()
    execution = InMemoryProgram3ExecutionRepository()
    ledger = InMemoryPublishingLedgerRepository()
    jobs_repo = InMemoryJobRepository()
    jobs = SharedJobEngine(jobs_repo, token_factory=lambda: "lease-token")
    decisions.put(selected())
    artifacts.put(artifact(artifact_state))
    service = Program3AuthoritativeService(
        decisions=decisions,
        artifacts=artifacts,
        execution=execution,
        ledger=ledger,
        jobs=jobs,
        guard=PublishingGuardEngine(),
        policy=Program3AuthorityPolicy(max_program2_handoff_age=handoff_age),
    )
    return service, ledger, jobs


def create_plan_and_started_job(service, jobs, *, valid_at: datetime = NOW):
    package = service.build_publish_plan(
        handoff=handoff(valid_at),
        plan_ref="program3-plan:1",
        publish_job_id="program3-job-1",
        target_account_id="publish-account-1",
        video_id="video-1",
        video_sha256=VIDEO_SHA,
        created_at=NOW,
        caption="Synthetic",
        tags=["#fixture"],
    )
    created = service.create_publish_job(
        plan_ref=package.plan_ref,
        idempotency_key="p3:video-1:publish-account-1",
        created_at=NOW,
    )
    assert created.state.value == "QUEUED"
    leased = jobs.lease_job(
        created.job_id,
        worker_id="worker-1",
        worker_capabilities={"android:publish"},
        at=NOW,
        lease_for=timedelta(minutes=5),
    )
    jobs.start_job(
        leased.job_id,
        worker_id="worker-1",
        lease_token=leased.lease_token,
        at=NOW,
    )
    return package


def test_happy_path_is_durable_and_confirmed_without_ui() -> None:
    service, ledger, jobs = build()
    package = create_plan_and_started_job(service, jobs)

    pre = service.pre_submit(
        publish_job_id=package.publish_plan.publish_job_id,
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
        evidence_refs=("scene-ready-1",),
    )
    assert pre.state is PreSubmitDecisionState.ALLOW_SUBMIT

    submitted = service.record_post_submitted(
        decision=pre,
        submitted_at=NOW + timedelta(minutes=1, seconds=1),
        idempotency_key="submit-attempt-1",
        evidence_refs=("tap-submit-1",),
    )
    assert service.execution.get_submission_for_job("program3-job-1") == submitted

    reconciliation = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=2),
        success_confirmed=True,
        evidence_refs=("success-signal-1",),
    )
    assert reconciliation.outcome is ReconciliationOutcome.CONFIRMED_SUCCESS
    assert reconciliation.retry_allowed is False

    entry = service.confirm_success(
        reconciliation=reconciliation,
        confirmed_at=NOW + timedelta(minutes=2),
    )
    assert entry.status == "CONFIRMED"
    assert ledger.history_for_video("video-1")[-1] == entry

    replay = service.confirm_success(
        reconciliation=reconciliation,
        confirmed_at=NOW + timedelta(minutes=3),
    )
    assert replay == entry


def test_duplicate_history_blocks_plan_creation() -> None:
    service, ledger, _jobs = build()
    ledger.append(
        PublishingLedgerEntry(
            publish_job_id="old-job",
            platform="shopee",
            target_account_id="old-account",
            video_id="video-1",
            video_sha256=VIDEO_SHA,
            status="CONFIRMED",
            updated_at=NOW - timedelta(days=1),
        )
    )
    with pytest.raises(ValueError, match="VIDEO_ALREADY_PUBLISHED"):
        service.build_publish_plan(
            handoff=handoff(),
            plan_ref="plan-1",
            publish_job_id="program3-job-1",
            target_account_id="publish-account-1",
            video_id="video-1",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )


def test_unvalidated_program2_artifact_blocks_plan() -> None:
    service, _ledger, _jobs = build(
        artifact_state=LinkArtifactValidationState.OUTCOME_UNKNOWN
    )
    with pytest.raises(ValueError, match="not validated"):
        service.build_publish_plan(
            handoff=handoff(),
            plan_ref="plan-1",
            publish_job_id="program3-job-1",
            target_account_id="publish-account-1",
            video_id="video-1",
            video_sha256=VIDEO_SHA,
            created_at=NOW,
        )


def test_pre_submit_fails_closed_for_scene_account_staleness_and_prior_submission() -> None:
    service, _ledger, jobs = build(handoff_age=timedelta(minutes=5))
    package = create_plan_and_started_job(service, jobs, valid_at=NOW)

    wrong_account = service.pre_submit(
        publish_job_id="program3-job-1",
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="wrong",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    assert wrong_account.state is PreSubmitDecisionState.REJECT
    assert "TARGET_ACCOUNT_MISMATCH" in wrong_account.reasons

    scene_unknown = service.pre_submit(
        publish_job_id="program3-job-1",
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=False,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    assert scene_unknown.state is PreSubmitDecisionState.NEEDS_HUMAN

    stale = service.pre_submit(
        publish_job_id="program3-job-1",
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=10),
    )
    assert stale.state is PreSubmitDecisionState.REJECT
    assert "PROGRAM2_HANDOFF_STALE" in stale.reasons

    good = service.pre_submit(
        publish_job_id="program3-job-1",
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    service.record_post_submitted(
        decision=good,
        submitted_at=NOW + timedelta(minutes=1, seconds=1),
        idempotency_key="submit-1",
    )
    again = service.pre_submit(
        publish_job_id="program3-job-1",
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=2),
    )
    assert again.state is PreSubmitDecisionState.REJECT
    assert "SUBMISSION_ALREADY_RECORDED" in again.reasons


def test_post_submitted_is_idempotent_and_conflicting_attempt_is_rejected() -> None:
    service, _ledger, jobs = build()
    package = create_plan_and_started_job(service, jobs)
    pre = service.pre_submit(
        publish_job_id=package.publish_plan.publish_job_id,
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    first = service.record_post_submitted(
        decision=pre,
        submitted_at=NOW + timedelta(minutes=1, seconds=1),
        idempotency_key="submit-1",
    )
    replay = service.record_post_submitted(
        decision=pre,
        submitted_at=NOW + timedelta(minutes=5),
        idempotency_key="submit-1",
    )
    assert replay == first
    with pytest.raises(ValueError, match="different submission"):
        service.record_post_submitted(
            decision=pre,
            submitted_at=NOW + timedelta(minutes=6),
            idempotency_key="submit-2",
        )


def test_reconciliation_never_blindly_retries_unknown_outcome() -> None:
    service, _ledger, jobs = build()
    package = create_plan_and_started_job(service, jobs)
    pre = service.pre_submit(
        publish_job_id=package.publish_plan.publish_job_id,
        worker_id="worker-1",
        lease_token="lease-token",
        device_id="device-1",
        target_account_id="publish-account-1",
        scene_ready=True,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    submitted = service.record_post_submitted(
        decision=pre,
        submitted_at=NOW + timedelta(minutes=1, seconds=1),
        idempotency_key="submit-1",
    )

    unknown = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=2),
    )
    assert unknown.outcome is ReconciliationOutcome.OUTCOME_UNKNOWN
    assert unknown.retry_allowed is False

    safe_retry = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=3),
        failure_safe_to_retry_confirmed=True,
        evidence_refs=("confirmed-not-posted",),
    )
    assert safe_retry.outcome is ReconciliationOutcome.CONFIRMED_FAILURE_SAFE_TO_RETRY
    assert safe_retry.retry_allowed is True

    human = service.reconcile(
        submission_id=submitted.submission_id,
        evaluated_at=NOW + timedelta(minutes=4),
        human_required=True,
    )
    assert human.outcome is ReconciliationOutcome.NEEDS_HUMAN
    assert human.retry_allowed is False

    with pytest.raises(ValueError, match="contradictory"):
        service.reconcile(
            submission_id=submitted.submission_id,
            evaluated_at=NOW + timedelta(minutes=5),
            success_confirmed=True,
            human_required=True,
        )

    with pytest.raises(ValueError, match="only CONFIRMED_SUCCESS"):
        service.confirm_success(
            reconciliation=unknown,
            confirmed_at=NOW + timedelta(minutes=6),
        )


def test_invalid_policy_fails_fast() -> None:
    with pytest.raises(ValueError):
        Program3AuthorityPolicy(version=" ")
    with pytest.raises(ValueError):
        Program3AuthorityPolicy(max_program2_handoff_age=timedelta(0))
