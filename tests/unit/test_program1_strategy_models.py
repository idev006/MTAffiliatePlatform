from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
    SignalValidationState,
)


NOW = datetime(2026, 9, 4, tzinfo=UTC)


def test_strategy_models_preserve_explicit_affiliate_decision_traceability() -> None:
    hypothesis = AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective="Find products worth testing",
        decision_question="Which products deserve affiliate effort now?",
        rationale="Focus scarce content effort on evidence-backed opportunities",
        target_outcome="candidate_hit_rate",
        audience_context="Thai gadget buyers",
        time_context="9.9 campaign",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )
    signal = SignalRequirement(
        signal_id="signal-demand",
        hypothesis_id=hypothesis.hypothesis_id,
        decision_supported=hypothesis.decision_question,
        expected_interpretation="rising demand may increase test priority",
        evidence_source="approved product observations",
        validation_state=SignalValidationState.LAB_VALIDATED,
        downstream_validation_metric="conversion_rate",
    )

    assert signal.hypothesis_id == hypothesis.hypothesis_id
    assert signal.validation_state is SignalValidationState.LAB_VALIDATED


def test_discovery_plan_rejects_duplicate_traceability_entries() -> None:
    with pytest.raises(ValidationError, match="required_signal_ids must be unique"):
        DiscoveryPlan(
            plan_id="plan-1",
            campaign_id="campaign-1",
            hypothesis_id="hyp-1",
            required_signal_ids=("signal-1", "signal-1"),
            source_scope="shopee",
            surface_scope=("search",),
            evidence_policy_version="evidence-v1",
            collection_policy_version="collection-v1",
            created_at=NOW,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("surface_scope", ("search", "search"), "surface_scope must be unique"),
        (
            "capability_requirements",
            ("collector:identity", "collector:identity"),
            "capability_requirements must be unique",
        ),
    ],
)
def test_discovery_plan_rejects_duplicate_scope_values(
    field: str, value: tuple[str, ...], message: str
) -> None:
    payload = {
        "plan_id": "plan-1",
        "campaign_id": "campaign-1",
        "hypothesis_id": "hyp-1",
        "required_signal_ids": ("signal-1",),
        "source_scope": "shopee",
        "surface_scope": ("search",),
        "capability_requirements": (),
        "evidence_policy_version": "evidence-v1",
        "collection_policy_version": "collection-v1",
        "created_at": NOW,
    }
    payload[field] = value
    with pytest.raises(ValidationError, match=message):
        DiscoveryPlan(**payload)
