from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.adapters.persistence.inmemory.program1_opportunity import (
    InMemoryProgram1OpportunityRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.application.program1_opportunity import Program1OpportunityService
from mtaffiliate.domain.job.models import JobEvent, JobRecord
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.domain.program1.opportunity import (
    OpportunityAction,
    OpportunityDecisionRecord,
    OpportunityEvidenceState,
    OpportunityThesis,
)
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityIntelligenceEngine,
)
from mtaffiliate.ports.repositories.program1_opportunity import (
    OpportunityDecisionConflictError,
)

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
KEY = ("shopee", "shop-1", "item-1")


def decision(
    decision_id: str,
    *,
    at: datetime = NOW,
    campaign_id: str = "campaign-1",
    action: OpportunityAction = OpportunityAction.TEST_NOW,
) -> OpportunityDecisionRecord:
    thesis = OpportunityThesis(
        product_key=KEY,
        product_name="Synthetic Product",
        as_of=at,
        feature_policy_version="features-lab-v1",
        qualification_policy_version="qualification-lab-v1",
        recommended_action=action,
        observed_evidence=("sold_signal=100",),
        evidence_state=OpportunityEvidenceState.SUFFICIENT_FOR_LAB,
        evidence_refs=("obs-1",),
    )
    return OpportunityDecisionRecord(
        decision_id=decision_id,
        campaign_id=campaign_id,
        hypothesis_id="hyp-1",
        source_job_id="job-1",
        evaluated_at=at,
        thesis=thesis,
    )


def service():
    products = InMemoryProductRepository()
    jobs = InMemoryJobRepository()
    strategies = InMemoryProgram1StrategyRepository()
    decisions = InMemoryProgram1OpportunityRepository()
    return (
        Program1OpportunityService(
            products=products,
            jobs=jobs,
            strategies=strategies,
            decisions=decisions,
            intelligence=OpportunityIntelligenceEngine(),
        ),
        products,
        jobs,
        strategies,
        decisions,
    )


def add_job(
    jobs: InMemoryJobRepository,
    *,
    job_id: str = "job-1",
    domain: str = "program1",
    job_type: str = "DISCOVER_PRODUCTS",
    payload_ref: str = "plan-ref",
) -> None:
    item = JobRecord(
        job_id=job_id,
        job_type=job_type,
        domain=domain,
        payload_ref=payload_ref,
        idempotency_key=f"idem:{job_id}",
        created_at=NOW,
        updated_at=NOW,
    )
    jobs.add_with_event(
        item,
        JobEvent(
            event_type="JOB_CREATED",
            job_id=job_id,
            job_version=1,
            emitted_at=NOW,
        ),
    )


def add_observation(
    products: InMemoryProductRepository,
    *,
    source_job_id: str | None,
    item_id: str = "item-1",
) -> None:
    products.add_observations(
        [
            ProductObservation(
                observation_id=f"obs:{item_id}",
                platform="shopee",
                shop_id="shop-1",
                item_id=item_id,
                collected_at=NOW,
                product_name="Synthetic Product",
                sold_signal=100,
                rating=4.8,
                review_count=100,
                source_job_id=source_job_id,
            )
        ]
    )


def test_inmemory_opportunity_repository_conflict_latest_and_campaign_ordering() -> None:
    repo = InMemoryProgram1OpportunityRepository()
    first = decision("d1", at=NOW)
    later = decision("d2", at=NOW + timedelta(minutes=1))
    other_campaign = decision(
        "d3",
        at=NOW + timedelta(minutes=2),
        campaign_id="campaign-2",
    )

    assert repo.get("missing") is None
    assert repo.latest_for_product(KEY) is None

    repo.put(first)
    repo.put(first)
    repo.put(later)
    repo.put(other_campaign)

    assert repo.get("d1") == first
    assert repo.latest_for_product(KEY) == other_campaign
    assert repo.list_for_campaign("campaign-1") == [later, first]
    assert repo.list_for_campaign("missing") == []

    with pytest.raises(OpportunityDecisionConflictError):
        repo.put(
            decision(
                "d1",
                at=NOW,
                action=OpportunityAction.HOLD,
            )
        )


def test_evaluate_product_rejects_missing_history_and_unattributed_latest() -> None:
    app, products, _jobs, _strategies, _decisions = service()

    with pytest.raises(KeyError):
        app.evaluate_product(KEY, evaluated_at=NOW)

    add_observation(products, source_job_id=None)
    with pytest.raises(ValueError, match="not traceable"):
        app.evaluate_product(KEY, evaluated_at=NOW)


def test_evaluate_product_rejects_missing_or_wrong_source_job() -> None:
    app, products, jobs, _strategies, _decisions = service()
    add_observation(products, source_job_id="job-1")

    with pytest.raises(ValueError, match="does not exist"):
        app.evaluate_product(KEY, evaluated_at=NOW)

    add_job(jobs, domain="program2")
    with pytest.raises(ValueError, match="not a Program 1 discovery job"):
        app.evaluate_product(KEY, evaluated_at=NOW)


def test_evaluate_product_rejects_missing_strategy_package() -> None:
    app, products, jobs, _strategies, _decisions = service()
    add_observation(products, source_job_id="job-1")
    add_job(jobs)

    with pytest.raises(ValueError, match="strategy work package is missing"):
        app.evaluate_product(KEY, evaluated_at=NOW)


def test_evaluate_campaign_validates_id_and_skips_unresolvable_products() -> None:
    app, products, jobs, _strategies, _decisions = service()

    with pytest.raises(ValueError, match="campaign_id must be non-empty"):
        app.evaluate_campaign("   ", evaluated_at=NOW)

    add_observation(products, source_job_id="missing", item_id="item-1")
    add_observation(products, source_job_id="wrong", item_id="item-2")
    add_job(jobs, job_id="wrong", domain="program2")

    assert app.evaluate_campaign("campaign-1", evaluated_at=NOW) == []


def test_qualified_handoff_excludes_non_test_actions() -> None:
    app, _products, _jobs, _strategies, decisions = service()
    decisions.put(decision("d1", action=OpportunityAction.WATCH))
    decisions.put(
        decision(
            "d2",
            at=NOW + timedelta(minutes=1),
            action=OpportunityAction.HOLD,
        )
    )

    assert app.qualified_handoffs("campaign-1") == []
