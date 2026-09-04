from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.domain.program1.opportunity import (
    OpportunityAction,
    OpportunityEvidenceState,
    QualificationState,
)
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityFeaturePolicy,
    OpportunityIntelligenceEngine,
    QualificationPolicy,
)

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def obs(
    observation_id: str,
    *,
    item_id: str = "item-1",
    at: datetime = NOW,
    sold: int | None = 100,
    rating: float | None = 4.5,
    reviews: int | None = 100,
    price: Decimal | None = Decimal(999),
) -> ProductObservation:
    return ProductObservation(
        observation_id=observation_id,
        platform="shopee",
        shop_id="shop-1",
        item_id=item_id,
        collected_at=at,
        product_name="Synthetic Product",
        price_current=price,
        sold_signal=sold,
        rating=rating,
        review_count=reviews,
        source_job_id="job-1",
    )


def test_features_preserve_history_and_momentum_without_total_score() -> None:
    engine = OpportunityIntelligenceEngine()
    history = [
        obs("obs-1", at=NOW - timedelta(days=1), sold=80),
        obs("obs-2", at=NOW, sold=120),
    ]

    features = engine.derive_features(history, as_of=NOW)

    assert features.history_count == 2
    assert features.latest_sold_signal == 120
    assert features.sold_signal_delta == 40
    assert features.evidence_state is OpportunityEvidenceState.SUFFICIENT_FOR_LAB
    assert "contentability" in features.unknown_features
    assert features.evidence_refs == ("obs-1", "obs-2")


def test_missing_core_evidence_requires_more_evidence() -> None:
    engine = OpportunityIntelligenceEngine()
    features = engine.derive_features(
        [obs("obs-1", sold=None, rating=None, reviews=None)],
        as_of=NOW,
    )
    decision = engine.qualify(features, evaluated_at=NOW)

    assert features.evidence_state is OpportunityEvidenceState.NEEDS_EVIDENCE
    assert decision.state is QualificationState.NEEDS_EVIDENCE
    assert decision.recommended_action is OpportunityAction.NEEDS_EVIDENCE
    assert any("unknown:demand" == risk for risk in decision.risks)


def test_stale_observation_requires_evidence_refresh() -> None:
    engine = OpportunityIntelligenceEngine(
        feature_policy=OpportunityFeaturePolicy(max_observation_age=timedelta(hours=1))
    )
    features = engine.derive_features(
        [obs("obs-1", at=NOW - timedelta(hours=2))],
        as_of=NOW,
    )
    decision = engine.qualify(features, evaluated_at=NOW)

    assert features.evidence_state is OpportunityEvidenceState.NEEDS_EVIDENCE
    assert decision.recommended_action is OpportunityAction.NEEDS_EVIDENCE


def test_low_rating_holds_candidate() -> None:
    engine = OpportunityIntelligenceEngine()
    decision = engine.qualify(
        engine.derive_features([obs("obs-1", rating=3.5)], as_of=NOW),
        evaluated_at=NOW,
    )

    assert decision.state is QualificationState.HOLD
    assert decision.recommended_action is OpportunityAction.HOLD
    assert "buyer_confidence_risk" in decision.risks


def test_thin_demand_or_reviews_watches_candidate() -> None:
    engine = OpportunityIntelligenceEngine(
        qualification_policy=QualificationPolicy(
            min_rating_for_test=4.0,
            min_reviews_for_test=50,
            min_sold_signal_for_test=100,
        )
    )
    decision = engine.qualify(
        engine.derive_features(
            [obs("obs-1", sold=20, rating=4.8, reviews=10)],
            as_of=NOW,
        ),
        evaluated_at=NOW,
    )

    assert decision.state is QualificationState.WATCH
    assert decision.recommended_action is OpportunityAction.WATCH


def test_core_evidence_can_qualify_only_for_controlled_test() -> None:
    engine = OpportunityIntelligenceEngine()
    history = [
        obs("obs-1", at=NOW - timedelta(days=1), sold=80),
        obs("obs-2", at=NOW, sold=120),
    ]

    thesis = engine.build_thesis(
        history,
        as_of=NOW,
        target_buyer_context="Thai gadget buyers",
    )

    assert thesis.recommended_action is OpportunityAction.TEST_NOW
    assert thesis.target_buyer_context == "Thai gadget buyers"
    assert thesis.feature_policy_version.endswith("lab-v1")
    assert thesis.qualification_policy_version.endswith("lab-v1")
    assert any("sold_signal_delta=40" == item for item in thesis.observed_evidence)
    assert any("not_yet_observed:contentability" == risk for risk in thesis.risks_and_uncertainties)


def test_declining_sold_signal_is_retained_as_risk() -> None:
    engine = OpportunityIntelligenceEngine()
    history = [
        obs("obs-1", at=NOW - timedelta(days=1), sold=200),
        obs("obs-2", at=NOW, sold=120),
    ]
    decision = engine.qualify(
        engine.derive_features(history, as_of=NOW),
        evaluated_at=NOW,
    )

    assert "observed_sold_signal_declined" in decision.risks


def test_mixed_product_history_is_rejected() -> None:
    engine = OpportunityIntelligenceEngine()
    with pytest.raises(ValueError, match="one product identity"):
        engine.derive_features(
            [obs("obs-1", item_id="a"), obs("obs-2", item_id="b")],
            as_of=NOW,
        )


def test_empty_history_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        OpportunityIntelligenceEngine().derive_features([], as_of=NOW)


@pytest.mark.parametrize(
    "policy",
    [
        lambda: OpportunityFeaturePolicy(version=" "),
        lambda: OpportunityFeaturePolicy(max_observation_age=timedelta(0)),
        lambda: QualificationPolicy(version=" "),
        lambda: QualificationPolicy(min_rating_for_test=6),
        lambda: QualificationPolicy(min_reviews_for_test=-1),
        lambda: QualificationPolicy(min_sold_signal_for_test=-1),
    ],
)
def test_invalid_policies_fail_fast(policy) -> None:
    with pytest.raises(ValueError):
        policy()
