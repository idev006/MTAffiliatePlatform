from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from mtaffiliate.domain.affiliate_offer.models import (
    LinkArtifactValidationState,
    Program3OfferHandoff,
)
from mtaffiliate.domain.job.models import JobRecord, JobState
from mtaffiliate.domain.publishing.models import (
    ApprovedOfferRef,
    PreSubmitDecision,
    PreSubmitDecisionState,
    Program3PlanPackage,
    PublishingLedgerEntry,
    PublishPlan,
    ReconciliationDecision,
    ReconciliationOutcome,
    SubmissionRecord,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.ports.repositories.program2_artifact import Program2ArtifactRepository
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionRepository
from mtaffiliate.ports.repositories.program3_execution import Program3ExecutionRepository
from mtaffiliate.ports.repositories.publishing import PublishingLedgerRepository


@dataclass(frozen=True)
class Program3AuthorityPolicy:
    version: str = "program3-authority-lab-v1"
    max_program2_handoff_age: timedelta = timedelta(hours=6)

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("Program 3 authority policy version must be non-empty")
        if self.max_program2_handoff_age <= timedelta(0):
            raise ValueError("max_program2_handoff_age must be positive")


class Program3AuthoritativeService:
    JOB_TYPE = "PUBLISH_CONTENT"
    DOMAIN = "program3"

    def __init__(
        self,
        *,
        decisions: Program2DecisionRepository,
        artifacts: Program2ArtifactRepository,
        execution: Program3ExecutionRepository,
        ledger: PublishingLedgerRepository,
        jobs: SharedJobEngine,
        guard: PublishingGuardEngine,
        policy: Program3AuthorityPolicy | None = None,
    ) -> None:
        self.decisions = decisions
        self.artifacts = artifacts
        self.execution = execution
        self.ledger = ledger
        self.jobs = jobs
        self.guard = guard
        self.policy = policy or Program3AuthorityPolicy()

    @staticmethod
    def _stable_id(prefix: str, payload: dict[str, object]) -> str:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        return f"{prefix}-{digest[:32]}"

    def build_publish_plan(
        self,
        *,
        handoff: Program3OfferHandoff,
        plan_ref: str,
        publish_job_id: str,
        target_account_id: str,
        video_id: str,
        video_sha256: str,
        created_at: datetime,
        caption: str = "",
        tags: list[str] | None = None,
        duplicate_policy_version: str = "publishing-duplicate-v1",
        plan_version: str = "program3-publish-plan-v1",
    ) -> Program3PlanPackage:
        if not plan_ref.strip():
            raise ValueError("plan_ref must be non-empty")
        decision = self.decisions.get(handoff.selection_decision_id)
        if decision is None:
            raise ValueError("Program 2 selection decision does not exist")
        artifact = self.artifacts.get(handoff.link_artifact_id)
        if artifact is None:
            raise ValueError("Program 2 link artifact does not exist")
        if decision.product_id != handoff.product_id:
            raise ValueError("Program 2 handoff product mismatch")
        if decision.preferred_offer_id != handoff.preferred_offer_id:
            raise ValueError("Program 2 handoff preferred offer mismatch")
        if decision.affiliate_account_id != handoff.affiliate_account_id:
            raise ValueError("Program 2 handoff affiliate account mismatch")
        if decision.backup_offer_ids != handoff.backup_offer_ids:
            raise ValueError("Program 2 handoff backup offer mismatch")
        handoff_age = created_at - handoff.valid_at
        if handoff_age < timedelta(0) or handoff_age > self.policy.max_program2_handoff_age:
            raise ValueError("Program 2 handoff is stale or has invalid time")
        if artifact.selection_decision_id != decision.decision_id:
            raise ValueError("link artifact does not belong to selection decision")
        if artifact.offer_id != decision.preferred_offer_id:
            raise ValueError("link artifact does not belong to preferred offer")
        if artifact.validation_state not in {
            LinkArtifactValidationState.LAB_VALIDATED,
            LinkArtifactValidationState.EVIDENCE_VALIDATED,
        }:
            raise ValueError("Program 2 link artifact is not validated for handoff")
        if artifact.validated_at is None:
            raise ValueError("Program 2 link artifact requires validated_at")

        platform, shop_id, item_id, offer_id, affiliate_account_id = (
            decision.preferred_commercial_key
        )
        approved = ApprovedOfferRef(
            selection_id=decision.decision_id,
            product_id=decision.product_id,
            offer_id=offer_id,
            shop_id=shop_id,
            item_id=item_id,
            affiliate_account_id=affiliate_account_id,
            affiliate_link_id=artifact.artifact_id,
        )
        plan = PublishPlan(
            publish_job_id=publish_job_id,
            platform=platform,
            target_account_id=target_account_id,
            video_id=video_id,
            video_sha256=video_sha256,
            offers=[approved],
            caption=caption,
            tags=tags or [],
            duplicate_policy_version=duplicate_policy_version,
            plan_version=plan_version,
            created_at=created_at,
        )
        duplicate = self.guard.evaluate_duplicate(
            plan,
            self.ledger.history_for_video(video_id),
        )
        if not duplicate.allowed:
            raise ValueError(duplicate.reason)

        package = Program3PlanPackage(
            plan_ref=plan_ref,
            source_program2_handoff_id=handoff.handoff_id,
            source_selection_decision_id=decision.decision_id,
            source_link_artifact_id=artifact.artifact_id,
            program2_handoff_valid_at=handoff.valid_at,
            publish_plan=plan,
            evidence_refs=tuple(sorted(set(handoff.evidence_refs) | set(artifact.evidence_refs))),
        )
        self.execution.put_plan(package)
        return package

    def create_publish_job(
        self,
        *,
        plan_ref: str,
        idempotency_key: str,
        created_at: datetime,
        priority: int = 0,
        capability_requirements: tuple[str, ...] = ("android:publish",),
    ) -> JobRecord:
        package = self.execution.get_plan(plan_ref)
        if package is None:
            raise ValueError(f"publish plan package is missing: {plan_ref}")
        plan = package.publish_plan
        created = self.jobs.create_job(
            job_id=plan.publish_job_id,
            job_type=self.JOB_TYPE,
            domain=self.DOMAIN,
            payload_ref=plan_ref,
            idempotency_key=idempotency_key,
            capability_requirements=capability_requirements,
            priority=priority,
            created_at=created_at,
        )
        if created.state is JobState.CREATED:
            return self.jobs.queue_job(created.job_id, at=created_at)
        return created

    def pre_submit(
        self,
        *,
        publish_job_id: str,
        worker_id: str,
        lease_token: str,
        device_id: str,
        target_account_id: str,
        scene_ready: bool,
        evaluated_at: datetime,
        evidence_refs: tuple[str, ...] = (),
    ) -> PreSubmitDecision:
        self.jobs.validate_active_execution(
            publish_job_id,
            worker_id=worker_id,
            lease_token=lease_token,
            at=evaluated_at,
        )
        job = self.jobs.repository.get(publish_job_id)
        if job is None:
            raise KeyError(publish_job_id)
        package = self.execution.get_plan(job.payload_ref)
        if package is None:
            raise ValueError(f"publish plan package is missing: {job.payload_ref}")
        plan = package.publish_plan

        reasons: list[str] = []
        state = PreSubmitDecisionState.ALLOW_SUBMIT
        if target_account_id != plan.target_account_id:
            state = PreSubmitDecisionState.REJECT
            reasons.append("TARGET_ACCOUNT_MISMATCH")
        if not scene_ready:
            state = PreSubmitDecisionState.NEEDS_HUMAN
            reasons.append("READY_TO_PUBLISH_SCENE_NOT_CONFIRMED")
        age = evaluated_at - package.program2_handoff_valid_at
        if age < timedelta(0) or age > self.policy.max_program2_handoff_age:
            state = PreSubmitDecisionState.REJECT
            reasons.append("PROGRAM2_HANDOFF_STALE")
        duplicate = self.guard.evaluate_duplicate(
            plan,
            self.ledger.history_for_video(plan.video_id),
        )
        if not duplicate.allowed:
            state = PreSubmitDecisionState.REJECT
            reasons.append(duplicate.reason)
        if self.execution.get_submission_for_job(publish_job_id) is not None:
            state = PreSubmitDecisionState.REJECT
            reasons.append("SUBMISSION_ALREADY_RECORDED")

        payload = {
            "job": publish_job_id,
            "worker": worker_id,
            "device": device_id,
            "account": target_account_id,
            "at": evaluated_at.isoformat(),
            "state": state.value,
            "reasons": reasons,
        }
        decision = PreSubmitDecision(
            decision_id=self._stable_id("p3pre", payload),
            publish_job_id=publish_job_id,
            plan_ref=package.plan_ref,
            worker_id=worker_id,
            device_id=device_id,
            target_account_id=target_account_id,
            evaluated_at=evaluated_at,
            state=state,
            reasons=tuple(reasons),
            evidence_refs=evidence_refs,
            policy_version=self.policy.version,
        )
        self.execution.put_pre_submit(decision)
        return decision

    def record_post_submitted(
        self,
        *,
        decision_id: str,
        lease_token: str,
        submitted_at: datetime,
        idempotency_key: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> SubmissionRecord:
        decision = self.execution.get_pre_submit(decision_id)
        if decision is None:
            raise ValueError("pre-submit decision does not exist")
        if decision.state is not PreSubmitDecisionState.ALLOW_SUBMIT:
            raise ValueError("POST_SUBMITTED requires ALLOW_SUBMIT decision")
        self.jobs.validate_active_execution(
            decision.publish_job_id,
            worker_id=decision.worker_id,
            lease_token=lease_token,
            at=submitted_at,
        )
        existing = self.execution.get_submission_for_job(decision.publish_job_id)
        if existing is not None:
            if existing.idempotency_key != idempotency_key:
                raise ValueError("publish job already has a different submission")
            return existing
        payload = {
            "job": decision.publish_job_id,
            "plan_ref": decision.plan_ref,
            "idempotency_key": idempotency_key,
        }
        record = SubmissionRecord(
            submission_id=self._stable_id("p3sub", payload),
            publish_job_id=decision.publish_job_id,
            plan_ref=decision.plan_ref,
            worker_id=decision.worker_id,
            device_id=decision.device_id,
            submitted_at=submitted_at,
            evidence_refs=tuple(sorted(set(decision.evidence_refs) | set(evidence_refs))),
            idempotency_key=idempotency_key,
        )
        self.execution.put_submission(record)
        package = self.execution.get_plan(decision.plan_ref)
        if package is None:
            raise ValueError("publish plan package does not exist")
        plan = package.publish_plan
        self.ledger.append(
            PublishingLedgerEntry(
                publish_job_id=plan.publish_job_id,
                platform=plan.platform,
                target_account_id=plan.target_account_id,
                video_id=plan.video_id,
                video_sha256=plan.video_sha256,
                status="POST_SUBMITTED",
                updated_at=submitted_at,
            )
        )
        self.jobs.record_checkpoint(
            decision.publish_job_id,
            worker_id=decision.worker_id,
            lease_token=lease_token,
            checkpoint_type="POST_SUBMITTED",
            payload={"submission_id": record.submission_id},
            at=submitted_at,
        )
        return record

    def reconcile(
        self,
        *,
        submission_id: str,
        evaluated_at: datetime,
        success_confirmed: bool = False,
        failure_safe_to_retry_confirmed: bool = False,
        human_required: bool = False,
        evidence_refs: tuple[str, ...] = (),
    ) -> ReconciliationDecision:
        submission = self.execution.get_submission(submission_id)
        if submission is None:
            raise ValueError("submission does not exist")
        flags = sum(
            bool(value)
            for value in (
                success_confirmed,
                failure_safe_to_retry_confirmed,
                human_required,
            )
        )
        if flags > 1:
            raise ValueError("reconciliation evidence is contradictory")
        if success_confirmed:
            outcome = ReconciliationOutcome.CONFIRMED_SUCCESS
        elif failure_safe_to_retry_confirmed:
            outcome = ReconciliationOutcome.CONFIRMED_FAILURE_SAFE_TO_RETRY
        elif human_required:
            outcome = ReconciliationOutcome.NEEDS_HUMAN
        else:
            outcome = ReconciliationOutcome.OUTCOME_UNKNOWN
        retry_allowed = outcome is ReconciliationOutcome.CONFIRMED_FAILURE_SAFE_TO_RETRY
        payload = {
            "submission": submission_id,
            "at": evaluated_at.isoformat(),
            "outcome": outcome.value,
            "evidence": evidence_refs,
        }
        decision = ReconciliationDecision(
            reconciliation_id=self._stable_id("p3rec", payload),
            submission_id=submission_id,
            publish_job_id=submission.publish_job_id,
            evaluated_at=evaluated_at,
            outcome=outcome,
            retry_allowed=retry_allowed,
            reasons=(outcome.value,),
            evidence_refs=evidence_refs,
            policy_version=self.policy.version,
        )
        self.execution.put_reconciliation(decision)
        package = self.execution.get_plan(submission.plan_ref)
        if package is None:
            raise ValueError("publish plan package does not exist")
        plan = package.publish_plan
        self.ledger.append(
            PublishingLedgerEntry(
                publish_job_id=plan.publish_job_id,
                platform=plan.platform,
                target_account_id=plan.target_account_id,
                video_id=plan.video_id,
                video_sha256=plan.video_sha256,
                status=outcome.value,
                updated_at=evaluated_at,
            )
        )
        return decision

    def confirm_success(
        self,
        *,
        reconciliation: ReconciliationDecision,
        confirmed_at: datetime,
    ) -> PublishingLedgerEntry:
        if reconciliation.outcome is not ReconciliationOutcome.CONFIRMED_SUCCESS:
            raise ValueError("only CONFIRMED_SUCCESS can finalize publishing ledger")
        submission = self.execution.get_submission(reconciliation.submission_id)
        if submission is None:
            raise ValueError("submission does not exist")
        package = self.execution.get_plan(submission.plan_ref)
        if package is None:
            raise ValueError("publish plan package does not exist")
        plan = package.publish_plan
        duplicate = self.guard.evaluate_duplicate(
            plan,
            self.ledger.history_for_video(plan.video_id),
        )
        if not duplicate.allowed:
            existing = [
                entry
                for entry in self.ledger.history_for_video(plan.video_id)
                if entry.publish_job_id == plan.publish_job_id
                and entry.status in self.guard.terminal_duplicate_statuses
            ]
            if existing:
                return existing[-1]
            raise ValueError(duplicate.reason)
        entry = PublishingLedgerEntry(
            publish_job_id=plan.publish_job_id,
            platform=plan.platform,
            target_account_id=plan.target_account_id,
            video_id=plan.video_id,
            video_sha256=plan.video_sha256,
            status="CONFIRMED",
            updated_at=confirmed_at,
        )
        self.ledger.append(entry)
        return entry
