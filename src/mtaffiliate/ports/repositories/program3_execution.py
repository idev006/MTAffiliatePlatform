from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.publishing.models import (
    Program3PlanPackage,
    ReconciliationDecision,
    SubmissionRecord,
)


class Program3ExecutionConflictError(RuntimeError):
    pass


class Program3ExecutionRepository(Protocol):
    def put_plan(self, package: Program3PlanPackage) -> None: ...
    def get_plan(self, plan_ref: str) -> Program3PlanPackage | None: ...

    def put_submission(self, submission: SubmissionRecord) -> None: ...
    def get_submission(self, submission_id: str) -> SubmissionRecord | None: ...
    def get_submission_for_job(self, publish_job_id: str) -> SubmissionRecord | None: ...

    def put_reconciliation(self, decision: ReconciliationDecision) -> None: ...
    def latest_reconciliation(self, submission_id: str) -> ReconciliationDecision | None: ...
