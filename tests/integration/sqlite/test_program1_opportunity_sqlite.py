from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.job import SQLAlchemyJobRepository
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.adapters.persistence.sqlalchemy.program1_opportunity import (
    SQLAlchemyProgram1OpportunityRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program1_strategy import (
    SQLAlchemyProgram1StrategyRepository,
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

pytestmark = pytest.mark.integration

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
URL = "sqlite:///data/program1-opportunity.db"


def compose(tmp_path):
    engine = build_engine(URL, project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    jobs_repo = SQLAlchemyJobRepository(sessions)
    strategy_repo = SQLAlchemyProgram1StrategyRepository(sessions)
    product_repo = SQLAlchemyProductRepository(sessions)
    decision_repo = SQLAlchemyProgram1OpportunityRepository(sessions)
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
    return engine, product_repo, discovery, opportunities, decision_repo


def seed(product_repo, discovery):
    hypothesis = AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective="Find controlled tests",
        decision_question="Which product deserves affiliate effort?",
        rationale="Evidence-first allocation",
        target_outcome="candidate_hit_rate",
        audience_context="Thai gadget buyers",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )
    discovery.create_discovery_job(
        hypothesis=hypothesis,
        signals=[
            SignalRequirement(
                signal_id="demand",
                hypothesis_id="hyp-1",
                decision_supported=hypothesis.decision_question,
                expected_interpretation="demand supports readiness",
                evidence_source="observations",
            )
        ],
        discovery_plan=DiscoveryPlan(
            plan_id="plan-1",
            campaign_id="campaign-1",
            hypothesis_id="hyp-1",
            required_signal_ids=("demand",),
            source_scope="synthetic",
            surface_scope=("search",),
            collection_targets=("https://example.invalid/search",),
            evidence_policy_version="evidence-v1",
            collection_policy_version="collection-v1",
            created_at=NOW,
        ),
        discovery_plan_ref="program1-plan:plan-1:v1",
        job_id="job-1",
        idempotency_key="campaign-1:plan-1",
        created_at=NOW,
    )
    product_repo.add_observations(
        [
            ProductObservation(
                observation_id="obs-1",
                platform="shopee",
                shop_id="shop-1",
                item_id="item-1",
                collected_at=NOW - timedelta(days=1),
                product_name="Synthetic SSD",
                price_current=Decimal("1590"),
                sold_signal=80,
                rating=4.8,
                review_count=100,
                source_job_id="job-1",
            ),
            ProductObservation(
                observation_id="obs-2",
                platform="shopee",
                shop_id="shop-1",
                item_id="item-1",
                collected_at=NOW,
                product_name="Synthetic SSD",
                price_current=Decimal("1590"),
                sold_signal=120,
                rating=4.8,
                review_count=120,
                source_job_id="job-1",
            ),
        ]
    )


def test_opportunity_decision_survives_restart_and_remains_handoff_ready(tmp_path) -> None:
    engine, products, discovery, opportunities, _decisions = compose(tmp_path)
    seed(products, discovery)

    decision = opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW)[0]
    assert decision.thesis.recommended_action is OpportunityAction.TEST_NOW
    engine.dispose()

    restarted_engine, _products, _discovery, restarted, decisions = compose(tmp_path)
    durable = decisions.get(decision.decision_id)
    assert durable == decision
    handoffs = restarted.qualified_handoffs("campaign-1")
    assert len(handoffs) == 1
    assert handoffs[0].decision_id == decision.decision_id
    assert handoffs[0].source_job_id == "job-1"
    restarted_engine.dispose()


def test_same_evaluation_is_idempotent(tmp_path) -> None:
    engine, products, discovery, opportunities, decisions = compose(tmp_path)
    seed(products, discovery)

    first = opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW)
    replay = opportunities.evaluate_campaign("campaign-1", evaluated_at=NOW)

    assert replay == first
    assert decisions.list_for_campaign("campaign-1") == first
    engine.dispose()


def test_product_history_preserves_source_job_provenance(tmp_path) -> None:
    engine, products, discovery, _opportunities, _decisions = compose(tmp_path)
    seed(products, discovery)

    history = products.observation_history(("shopee", "shop-1", "item-1"))
    assert [item.source_job_id for item in history] == ["job-1", "job-1"]
    assert [item.observation_id for item in history] == ["obs-1", "obs-2"]
    engine.dispose()
