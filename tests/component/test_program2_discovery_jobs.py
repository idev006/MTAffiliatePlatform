from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.program2_work import InMemoryProgram2WorkRepository
from mtaffiliate.application.program2_jobs import Program2OfferDiscoveryJobService
from mtaffiliate.domain.affiliate_offer.models import OfferDiscoveryPlan
from mtaffiliate.domain.job.models import JobState
from mtaffiliate.domain.program1.opportunity import (
    OpportunityAction,
    QualifiedOpportunityHandoff,
)
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

NOW = datetime(2026, 9, 4, 15, 30, tzinfo=UTC)


def handoff(
    *,
    action: OpportunityAction = OpportunityAction.TEST_NOW,
) -> QualifiedOpportunityHandoff:
    return QualifiedOpportunityHandoff(
        handoff_id="p1h-decision-1",
        decision_id="decision-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        source_job_id="program1-job-1",
        product_key=("shopee", "shop-1", "item-1"),
        product_name="Synthetic SSD",
        recommended_action=action,
        evidence_refs=("obs-1", "obs-2"),
        feature_policy_version="p1-features-v1",
        qualification_policy_version="p1-qualification-v1",
    )


def plan(**overrides) -> OfferDiscoveryPlan:
    values = {
        "plan_id": "offer-plan-1",
        "campaign_id": "campaign-1",
        "hypothesis_id": "hyp-1",
        "source_program1_decision_id": "decision-1",
        "product_key": ("shopee", "shop-1", "item-1"),
        "product_name": "Synthetic SSD",
        "affiliate_account_id": "affiliate-account-1",
        "collection_targets": ("https://example.invalid/affiliate/search?q=ssd",),
        "capability_requirements": ("offer:candidate-read",),
        "evidence_policy_version": "program2-evidence-v1",
        "collection_policy_version": "program2-collection-v1",
        "created_at": NOW,
    }
    values.update(overrides)
    return OfferDiscoveryPlan(**values)


def build() -> tuple[
    Program2OfferDiscoveryJobService,
    InMemoryProgram2WorkRepository,
    InMemoryJobRepository,
]:
    jobs_repo = InMemoryJobRepository()
    work_repo = InMemoryProgram2WorkRepository()
    jobs = SharedJobEngine(jobs_repo, token_factory=lambda: "lease-token")
    return Program2OfferDiscoveryJobService(work_repo, jobs), work_repo, jobs_repo


def test_qualified_handoff_creates_queued_offer_discovery_job_and_durable_work() -> None:
    service, work_repo, jobs_repo = build()
    created = service.create_offer_discovery_job(
        handoff=handoff(),
        discovery_plan=plan(),
        work_ref="program2-work:offer-plan-1:v1",
        job_id="program2-job-1",
        idempotency_key="campaign-1:decision-1:affiliate-account-1",
        created_at=NOW,
    )

    assert created.state is JobState.QUEUED
    assert created.domain == "program2"
    assert created.job_type == "DISCOVER_AFFILIATE_OFFERS"
    assert created.capability_requirements == ("offer:candidate-read",)
    assert jobs_repo.get("program2-job-1") == created

    package = service.get_work_package("program2-job-1")
    assert package == work_repo.get("program2-work:offer-plan-1:v1")
    assert package.upstream_decision_id == "decision-1"
    assert package.upstream_source_job_id == "program1-job-1"
    assert package.affiliate_account_id == "affiliate-account-1"


def test_same_logical_creation_is_idempotent() -> None:
    service, _work_repo, _jobs_repo = build()
    kwargs = dict(
        handoff=handoff(),
        discovery_plan=plan(),
        work_ref="program2-work:offer-plan-1:v1",
        job_id="program2-job-1",
        idempotency_key="campaign-1:decision-1:affiliate-account-1",
        created_at=NOW,
    )

    first = service.create_offer_discovery_job(**kwargs)
    replay = service.create_offer_discovery_job(**kwargs)

    assert replay.job_id == first.job_id
    assert replay.state is JobState.QUEUED


@pytest.mark.parametrize(
    ("bad_handoff", "bad_plan", "message"),
    [
        (
            handoff(action=OpportunityAction.WATCH),
            plan(),
            "only TEST_NOW",
        ),
        (
            handoff(),
            plan(campaign_id="other"),
            "campaign must match",
        ),
        (
            handoff(),
            plan(hypothesis_id="other"),
            "hypothesis must match",
        ),
        (
            handoff(),
            plan(source_program1_decision_id="other"),
            "must reference the Program 1 decision",
        ),
        (
            handoff(),
            plan(product_key=("shopee", "shop-1", "other")),
            "product identity must match",
        ),
        (
            handoff(),
            plan(product_name="Other"),
            "product name must match",
        ),
    ],
)
def test_invalid_upstream_or_plan_traceability_is_rejected(
    bad_handoff: QualifiedOpportunityHandoff,
    bad_plan: OfferDiscoveryPlan,
    message: str,
) -> None:
    service, _work_repo, _jobs_repo = build()
    with pytest.raises(ValueError, match=message):
        service.create_offer_discovery_job(
            handoff=bad_handoff,
            discovery_plan=bad_plan,
            work_ref="program2-work:offer-plan-1:v1",
            job_id="program2-job-1",
            idempotency_key="idem",
            created_at=NOW,
        )


def test_blank_work_ref_is_rejected() -> None:
    service, _work_repo, _jobs_repo = build()
    with pytest.raises(ValueError, match="work_ref"):
        service.create_offer_discovery_job(
            handoff=handoff(),
            discovery_plan=plan(),
            work_ref=" ",
            job_id="program2-job-1",
            idempotency_key="idem",
            created_at=NOW,
        )


def test_work_package_query_rejects_missing_or_wrong_job() -> None:
    service, _work_repo, jobs_repo = build()
    with pytest.raises(KeyError):
        service.get_work_package("missing")

    shared = service.jobs
    shared.create_job(
        job_id="program1-job",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="x",
        idempotency_key="x",
        created_at=NOW,
    )
    assert jobs_repo.get("program1-job") is not None
    with pytest.raises(ValueError, match="not a Program 2"):
        service.get_work_package("program1-job")
