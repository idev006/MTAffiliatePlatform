from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program3_execution import (
    SQLAlchemyProgram3ExecutionRepository,
)
from mtaffiliate.domain.publishing.models import (
    ApprovedOfferRef,
    PreSubmitDecision,
    PreSubmitDecisionState,
    Program3PlanPackage,
    PublishPlan,
    ReconciliationDecision,
    ReconciliationOutcome,
    SubmissionRecord,
)
from mtaffiliate.ports.repositories.program3_execution import Program3ExecutionConflictError

pytestmark = pytest.mark.integration
NOW = datetime(2026, 9, 4, 20, 0, tzinfo=UTC)
URL = "sqlite:///data/program3-authority.db"


def compose(root: Path):
    engine = build_engine(URL, project_root=root)
    Base.metadata.create_all(engine)
    return engine, SQLAlchemyProgram3ExecutionRepository(build_session_factory(engine))


def package(plan_ref: str = "plan-1") -> Program3PlanPackage:
    return Program3PlanPackage(
        plan_ref=plan_ref,
        source_program2_handoff_id="p2h-1",
        source_selection_decision_id="p2d-1",
        source_link_artifact_id="link-1",
        program2_handoff_valid_at=NOW,
        publish_plan=PublishPlan(
            publish_job_id="program3-job-1",
            platform="shopee",
            target_account_id="publish-account-1",
            video_id="video-1",
            video_sha256="a" * 64,
            offers=[
                ApprovedOfferRef(
                    selection_id="p2d-1",
                    product_id="shopee:shop-1:item-1",
                    offer_id="offer-1",
                    shop_id="shop-1",
                    item_id="item-1",
                    affiliate_account_id="affiliate-account-1",
                    affiliate_link_id="link-1",
                )
            ],
            duplicate_policy_version="duplicate-v1",
            plan_version="plan-v1",
            created_at=NOW,
        ),
        evidence_refs=("evidence-1",),
    )



def pre_submit() -> PreSubmitDecision:
    return PreSubmitDecision(
        decision_id="p3pre-1",
        publish_job_id="program3-job-1",
        plan_ref="plan-1",
        worker_id="worker-1",
        device_id="device-1",
        target_account_id="publish-account-1",
        evaluated_at=NOW + timedelta(seconds=30),
        state=PreSubmitDecisionState.ALLOW_SUBMIT,
        reasons=(),
        evidence_refs=("scene-ready",),
        policy_version="program3-authority-lab-v1",
    )

def submission() -> SubmissionRecord:
    return SubmissionRecord(
        submission_id="p3sub-1",
        publish_job_id="program3-job-1",
        plan_ref="plan-1",
        worker_id="worker-1",
        device_id="device-1",
        submitted_at=NOW + timedelta(minutes=1),
        evidence_refs=("submit-evidence",),
        idempotency_key="submit-1",
    )


def reconciliation() -> ReconciliationDecision:
    return ReconciliationDecision(
        reconciliation_id="p3rec-1",
        submission_id="p3sub-1",
        publish_job_id="program3-job-1",
        evaluated_at=NOW + timedelta(minutes=2),
        outcome=ReconciliationOutcome.OUTCOME_UNKNOWN,
        retry_allowed=False,
        reasons=("OUTCOME_UNKNOWN",),
        evidence_refs=("reconcile-evidence",),
        policy_version="program3-authority-lab-v1",
    )


def test_program3_execution_state_survives_restart(tmp_path: Path) -> None:
    engine, repo = compose(tmp_path)
    repo.put_plan(package())
    repo.put_pre_submit(pre_submit())
    repo.put_submission(submission())
    repo.put_reconciliation(reconciliation())
    engine.dispose()

    restarted_engine, restarted = compose(tmp_path)
    assert restarted.get_plan("plan-1") == package()
    assert restarted.get_pre_submit("p3pre-1") == pre_submit()
    assert restarted.get_submission("p3sub-1") == submission()
    assert restarted.get_submission_for_job("program3-job-1") == submission()
    assert restarted.latest_reconciliation("p3sub-1") == reconciliation()
    restarted_engine.dispose()


def test_program3_sql_repository_is_idempotent_and_conflict_safe(tmp_path: Path) -> None:
    engine, repo = compose(tmp_path)
    plan = package()
    repo.put_plan(plan)
    repo.put_plan(plan)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_plan(plan.model_copy(update={"evidence_refs": ("different",)}))

    pre = pre_submit()
    repo.put_pre_submit(pre)
    repo.put_pre_submit(pre)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_pre_submit(pre.model_copy(update={"device_id": "different"}))
    assert repo.get_pre_submit("missing") is None

    submitted = submission()
    repo.put_submission(submitted)
    repo.put_submission(submitted)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_submission(submitted.model_copy(update={"device_id": "different"}))

    rec = reconciliation()
    repo.put_reconciliation(rec)
    repo.put_reconciliation(rec)
    with pytest.raises(Program3ExecutionConflictError):
        repo.put_reconciliation(rec.model_copy(update={"retry_allowed": True}))

    assert repo.get_plan("missing") is None
    assert repo.get_submission("missing") is None
    assert repo.get_submission_for_job("missing") is None
    assert repo.latest_reconciliation("missing") is None
    engine.dispose()
