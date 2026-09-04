from datetime import UTC, datetime

import pytest

from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)


NOW = datetime(2026, 9, 4, tzinfo=UTC)


def hypothesis() -> AffiliateSuccessHypothesis:
    return AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective="Find products worth testing",
        decision_question="Which products deserve affiliate effort now?",
        rationale="Concentrate content effort",
        target_outcome="candidate_hit_rate",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )


def signal(signal_id: str = "demand") -> SignalRequirement:
    return SignalRequirement(
        signal_id=signal_id,
        hypothesis_id="hyp-1",
        decision_supported="Which products deserve affiliate effort now?",
        expected_interpretation="higher evidence-backed demand increases test priority",
        evidence_source="product observations",
    )


def plan(*signal_ids: str) -> DiscoveryPlan:
    return DiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        required_signal_ids=signal_ids,
        source_scope="shopee",
        surface_scope=("search", "product_detail"),
        capability_requirements=("collector:identity",),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=NOW,
    )


def test_planner_builds_ordered_strategy_to_work_contract() -> None:
    result = Program1StrategyPlanner().build(
        hypothesis=hypothesis(),
        signals=[signal("contentability"), signal("demand")],
        discovery_plan=plan("demand", "contentability"),
    )

    assert [item.signal_id for item in result.signals] == ["demand", "contentability"]
    assert result.discovery_plan.hypothesis_id == result.hypothesis.hypothesis_id


def test_planner_rejects_unknown_required_signal() -> None:
    with pytest.raises(ValueError, match="unknown required signals"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[signal("demand")],
            discovery_plan=plan("demand", "momentum"),
        )


def test_planner_rejects_cross_hypothesis_signal() -> None:
    wrong = signal("demand").model_copy(update={"hypothesis_id": "hyp-other"})
    with pytest.raises(ValueError, match="must reference the supplied hypothesis"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[wrong],
            discovery_plan=plan("demand"),
        )


def test_planner_rejects_unplanned_signal_to_prevent_collect_because_available() -> None:
    with pytest.raises(ValueError, match="not required by discovery plan"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[signal("demand"), signal("rating")],
            discovery_plan=plan("demand"),
        )


def test_planner_rejects_campaign_mismatch() -> None:
    mismatched = plan("demand").model_copy(update={"campaign_id": "campaign-other"})
    with pytest.raises(ValueError, match="campaign must match"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[signal("demand")],
            discovery_plan=mismatched,
        )


def test_planner_rejects_plan_for_other_hypothesis() -> None:
    mismatched = plan("demand").model_copy(update={"hypothesis_id": "hyp-other"})
    with pytest.raises(ValueError, match="must reference the supplied hypothesis"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[signal("demand")],
            discovery_plan=mismatched,
        )


def test_planner_rejects_duplicate_signal_ids() -> None:
    with pytest.raises(ValueError, match="duplicate signal_id"):
        Program1StrategyPlanner().build(
            hypothesis=hypothesis(),
            signals=[signal("demand"), signal("demand")],
            discovery_plan=plan("demand"),
        )
