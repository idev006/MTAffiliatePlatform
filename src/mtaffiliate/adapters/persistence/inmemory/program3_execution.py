from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.publishing.models import (
    Program3PlanPackage,
    ReconciliationDecision,
    SubmissionRecord,
)
from mtaffiliate.ports.repositories.program3_execution import Program3ExecutionConflictError


class InMemoryProgram3ExecutionRepository:
    def __init__(self) -> None:
        self._plans: dict[str, Program3PlanPackage] = {}
        self._submissions: dict[str, SubmissionRecord] = {}
        self._submission_by_job: dict[str, str] = {}
        self._reconciliations: dict[str, ReconciliationDecision] = {}
        self._lock = RLock()

    def put_plan(self, package: Program3PlanPackage) -> None:
        with self._lock:
            existing = self._plans.get(package.plan_ref)
            if existing is not None and existing != package:
                raise Program3ExecutionConflictError(f"plan conflict: {package.plan_ref}")
            self._plans[package.plan_ref] = package

    def get_plan(self, plan_ref: str) -> Program3PlanPackage | None:
        with self._lock:
            return self._plans.get(plan_ref)

    def put_submission(self, submission: SubmissionRecord) -> None:
        with self._lock:
            existing = self._submissions.get(submission.submission_id)
            if existing is not None and existing != submission:
                raise Program3ExecutionConflictError(
                    f"submission conflict: {submission.submission_id}"
                )
            existing_job_id = self._submission_by_job.get(submission.publish_job_id)
            if existing_job_id is not None and existing_job_id != submission.submission_id:
                raise Program3ExecutionConflictError(
                    f"publish job already has submission: {submission.publish_job_id}"
                )
            self._submissions[submission.submission_id] = submission
            self._submission_by_job[submission.publish_job_id] = submission.submission_id

    def get_submission(self, submission_id: str) -> SubmissionRecord | None:
        with self._lock:
            return self._submissions.get(submission_id)

    def get_submission_for_job(self, publish_job_id: str) -> SubmissionRecord | None:
        with self._lock:
            submission_id = self._submission_by_job.get(publish_job_id)
            return None if submission_id is None else self._submissions[submission_id]

    def put_reconciliation(self, decision: ReconciliationDecision) -> None:
        with self._lock:
            existing = self._reconciliations.get(decision.reconciliation_id)
            if existing is not None and existing != decision:
                raise Program3ExecutionConflictError(
                    f"reconciliation conflict: {decision.reconciliation_id}"
                )
            self._reconciliations[decision.reconciliation_id] = decision

    def latest_reconciliation(self, submission_id: str) -> ReconciliationDecision | None:
        with self._lock:
            candidates = [
                decision
                for decision in self._reconciliations.values()
                if decision.submission_id == submission_id
            ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (item.evaluated_at, item.reconciliation_id),
        )
