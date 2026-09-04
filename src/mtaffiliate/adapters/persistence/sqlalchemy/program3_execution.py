from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.publishing.models import (
    Program3PlanPackage,
    ReconciliationDecision,
    SubmissionRecord,
)
from mtaffiliate.ports.repositories.program3_execution import Program3ExecutionConflictError

from .models import (
    Program3PlanRow,
    Program3ReconciliationRow,
    Program3SubmissionRow,
)


class SQLAlchemyProgram3ExecutionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fingerprint_json(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def put_plan(self, package: Program3PlanPackage) -> None:
        raw = package.model_dump_json()
        fingerprint = self._fingerprint_json(raw)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program3PlanRow, package.plan_ref)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program3ExecutionConflictError(
                        f"plan conflict: {package.plan_ref}"
                    )
                return
            duplicate_job = session.scalar(
                select(Program3PlanRow).where(
                    Program3PlanRow.publish_job_id == package.publish_plan.publish_job_id
                )
            )
            if duplicate_job is not None:
                raise Program3ExecutionConflictError(
                    f"publish job already has plan: {package.publish_plan.publish_job_id}"
                )
            session.add(
                Program3PlanRow(
                    plan_ref=package.plan_ref,
                    publish_job_id=package.publish_plan.publish_job_id,
                    package_json=raw,
                    fingerprint=fingerprint,
                    created_at=package.publish_plan.created_at,
                )
            )

    def get_plan(self, plan_ref: str) -> Program3PlanPackage | None:
        with self._session_factory() as session:
            row = session.get(Program3PlanRow, plan_ref)
            return None if row is None else Program3PlanPackage.model_validate_json(row.package_json)

    def put_submission(self, submission: SubmissionRecord) -> None:
        raw = submission.model_dump_json()
        fingerprint = self._fingerprint_json(raw)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program3SubmissionRow, submission.submission_id)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program3ExecutionConflictError(
                        f"submission conflict: {submission.submission_id}"
                    )
                return
            existing_job = session.scalar(
                select(Program3SubmissionRow).where(
                    Program3SubmissionRow.publish_job_id == submission.publish_job_id
                )
            )
            if existing_job is not None:
                raise Program3ExecutionConflictError(
                    f"publish job already has submission: {submission.publish_job_id}"
                )
            session.add(
                Program3SubmissionRow(
                    submission_id=submission.submission_id,
                    publish_job_id=submission.publish_job_id,
                    record_json=raw,
                    fingerprint=fingerprint,
                    submitted_at=submission.submitted_at,
                )
            )

    def get_submission(self, submission_id: str) -> SubmissionRecord | None:
        with self._session_factory() as session:
            row = session.get(Program3SubmissionRow, submission_id)
            return None if row is None else SubmissionRecord.model_validate_json(row.record_json)

    def get_submission_for_job(self, publish_job_id: str) -> SubmissionRecord | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(Program3SubmissionRow).where(
                    Program3SubmissionRow.publish_job_id == publish_job_id
                )
            )
            return None if row is None else SubmissionRecord.model_validate_json(row.record_json)

    def put_reconciliation(self, decision: ReconciliationDecision) -> None:
        raw = decision.model_dump_json()
        fingerprint = self._fingerprint_json(raw)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program3ReconciliationRow, decision.reconciliation_id)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program3ExecutionConflictError(
                        f"reconciliation conflict: {decision.reconciliation_id}"
                    )
                return
            session.add(
                Program3ReconciliationRow(
                    reconciliation_id=decision.reconciliation_id,
                    submission_id=decision.submission_id,
                    decision_json=raw,
                    fingerprint=fingerprint,
                    evaluated_at=decision.evaluated_at,
                )
            )

    def latest_reconciliation(self, submission_id: str) -> ReconciliationDecision | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(Program3ReconciliationRow)
                .where(Program3ReconciliationRow.submission_id == submission_id)
                .order_by(
                    Program3ReconciliationRow.evaluated_at.desc(),
                    Program3ReconciliationRow.reconciliation_id.desc(),
                )
            )
            return None if row is None else ReconciliationDecision.model_validate_json(
                row.decision_json
            )
