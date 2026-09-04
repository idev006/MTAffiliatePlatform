from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.adapters.persistence.inmemory.program1_opportunity import (
    InMemoryProgram1OpportunityRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_opportunity import Program1OpportunityService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.domain.program1.opportunity import OpportunityAction
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityIntelligenceEngine,
)
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def build():
    jobs_repo = InMemoryJobRepository()
    strategy_repo = InMemoryProgram1StrategyRepository()
    product_repo = InMemoryProductRepository()
    decision_repo = InMemoryProgram1OpportunityRepository()
    jobs = SharedJobEngine(jobs_repo, token_factory=lambda: "lease-1")
    discovery = Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        strategy_repo,
        jobs,
    )
    opportunities = Program1OpportunityService(
        products=product_repo,
        jobs=jobs_repo,
        strategies=strategy_repo,
        decisions=decision_repo,
        intelligence=OpportunityIntelligenceEngine(),
    )
    return product_repo, discovery, opportunities


def create_job(discovery: Program1DiscoveryJobService):
    hypothesis = AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective="Find controlled affiliate tests",
        decision_question="Which products deserve affiliate effort now?",
        rationale="Reduce wasted content effort",
        target_outcome="candidate_hit_rate",
        audience_context="Thai gadget buyers",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )
    signals = [
        SignalRequirement(
            signal_id="demand",
            hypothesis_id="hyp-1",
            decision_supported=hypothesis.decision_question,
            expected_interpretation="demand supports test readiness",
            evidence_source="approved observations",
        )
    ]
    plan = DiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        required_signal_ids=("demand",),
        source_scope="synthetic",
        surface_scope=("search",),
        collection_targets=("https://example.invalid/search?q=ssd",),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=NOW,
    )
    return discovery.create_discovery_job(
        hypothesis=hypothesis,
        signals=signals,
        discovery_plan=plan,
        discovery_plan_ref="program1-plan:plan-1:v1",
        job_id="job-1",
        idempotency_key="campaign-1:plan-1",
        created_at=NOW,
    )


def observation(
    observation_id: str,
    *,
    at: datetime,
    sold: int,
    rating: float,
    reviews: int,
) -> ProductObservation:
    return ProductObservation(
        observation_id=observation_id,
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        collected_at=at,
        product_name="Synthetic SSD",
        price_current=Decimal(1590),
        sold_signal=sold,
        rating=rating,
        review_count=reviews,
        source_worker_id="worker-1",
        source_job_id="job-1",
    )


def test_campaign_evaluation_builds_traceable_qualified_handoff() -> None:
    products, discovery, opportunities = build()
    create_job(discovery)
    products.add_observations(
        [
            observation(
                "obs-1",
                at=NOW - timedelta(days=1),
                sold=80,
                rating=4.8,
                reviews=100,
            ),
            observation(
                "obs-2",
                at=NOW,
                sold=120,
                rating=4.8,
                reviews=120,
            ),
        ]
    )

    decisions = opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW)
    assert len(decisions) == 1
    decision = decisions[0]
    assert decision.campaign_id == "campaign-1"
    assert decision.hypothesis_id == "hyp-1"
    assert decision.source_job_id == "job-1"
    assert decision.thesis.recommended_action is OpportunityAction.TEST_NOW
    assert decision.thesis.target_buyer_context == "Thai gadget buyers"
    assert decision.thesis.evidence_refs == ("obs-1", "obs-2")

    handoffs = opportunities.qualified_handoffs("campaign-1")
    assert len(handoffs) == 1
    assert handoffs[0].decision_id == decision.decision_id
    assert handoffs[0].product_key == ("shopee", "shop-1", "item-1")


def test_latest_nonqualified_decision_suppresses_older_handoff() -> None:
    products, discovery, opportunities = build()
    create_job(discovery)
    products.add_observations(
        [
            observation(
                "obs-1",
                at=NOW,
                sold=120,
                rating=4.8,
                reviews=120,
            )
        ]
    )
    first = opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW)
    assert first[0].thesis.recommended_action is OpportunityAction.TEST_NOW
    assert len(opportunities.qualified_handoffs("campaign-1")) == 1

    products.add_observations(
        [
            observation(
                "obs-2",
                at=NOW + timedelta(hours=1),
                sold=125,
                rating=4.8,
                reviews=5,
            )
        ]
    )
    second = opportunities.evaluate_campaign(
        "campaign-1",
        evaluated_at=NOW + timedelta(hours=1),
    )
    assert second[0].thesis.recommended_action is OpportunityAction.WATCH
    assert opportunities.qualified_handoffs("campaign-1") == []


def test_unattributed_observation_is_not_silently_evaluated_for_campaign() -> None:
    products, _discovery, opportunities = build()
    products.add_observations(
        [
            ProductObservation(
                observation_id="legacy-1",
                platform="shopee",
                shop_id="shop-x",
                item_id="item-x",
                collected_at=NOW,
                product_name="Legacy product",
                sold_signal=999,
                rating=5,
                review_count=999,
            )
        ]
    )

    assert opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW) == []
