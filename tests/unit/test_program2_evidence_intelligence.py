from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferEvidenceState,
    OfferQualificationState,
    OfferRecommendedAction,
)
from mtaffiliate.engines.affiliate_offer_engine.service import (
    EvidenceFirstOfferIntelligence,
    OfferFeaturePolicy,
    OfferQualificationPolicy,
)

NOW = datetime(2026, 9, 4, 16, 0, tzinfo=UTC)


def offer(
    observation_id: str = "offer-obs-1",
    *,
    observed_at: datetime = NOW,
    available: bool = True,
    commission: float | None = 10.0,
    extra: float | None = 2.0,
    rating: float | None = 4.8,
    reviews: int | None = 100,
    sold: int | None = 200,
    session_context_id: str | None = "session-1",
) -> AffiliateOfferObservation:
    return AffiliateOfferObservation(
        observation_id=observation_id,
        offer_id="offer-1",
        product_id="shopee:shop-1:item-1",
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        affiliate_account_id="account-1",
        session_context_id=session_context_id,
        source_worker_id="worker-1",
        source_job_id="job-1",
        extractor_version="fixture-v1",
        observed_at=observed_at,
        seller_name="Seller",
        product_name="Synthetic SSD",
        price_current=Decimal(1590),
        commission_rate=commission,
        extra_commission_rate=extra,
        rating=rating,
        review_count=reviews,
        sold_signal=sold,
        available=available,
    )


def test_complete_fresh_offer_is_sufficient_for_lab() -> None:
    engine = EvidenceFirstOfferIntelligence()
    features = engine.derive_features(offer(), as_of=NOW)
    decision = engine.qualify(features, evaluated_at=NOW)

    assert features.evidence_state is OfferEvidenceState.SUFFICIENT_FOR_LAB
    assert features.commission_total_rate == 12.0
    assert decision.state is OfferQualificationState.QUALIFIED
    assert decision.recommended_action is OfferRecommendedAction.SELECT_NOW


def test_stale_offer_requires_refresh() -> None:
    engine = EvidenceFirstOfferIntelligence(
        feature_policy=OfferFeaturePolicy(max_observation_age=timedelta(hours=1))
    )
    features = engine.derive_features(
        offer(observed_at=NOW - timedelta(hours=2)),
        as_of=NOW,
    )
    decision = engine.qualify(features, evaluated_at=NOW)

    assert features.evidence_state is OfferEvidenceState.STALE
    assert decision.recommended_action is OfferRecommendedAction.NEEDS_EVIDENCE
    assert "freshness" in decision.risks


def test_missing_economics_requires_evidence() -> None:
    engine = EvidenceFirstOfferIntelligence()
    features = engine.derive_features(
        offer(commission=None, extra=None, rating=None, reviews=None),
        as_of=NOW,
    )
    decision = engine.qualify(features, evaluated_at=NOW)

    assert features.evidence_state is OfferEvidenceState.NEEDS_EVIDENCE
    assert "commission" in features.unknown_features
    assert "rating" in features.unknown_features
    assert decision.state is OfferQualificationState.NEEDS_EVIDENCE


def test_unavailable_offer_is_rejected_before_economics() -> None:
    engine = EvidenceFirstOfferIntelligence()
    decision = engine.qualify(
        engine.derive_features(offer(available=False), as_of=NOW),
        evaluated_at=NOW,
    )
    assert decision.state is OfferQualificationState.REJECTED
    assert decision.recommended_action is OfferRecommendedAction.REJECT


def test_low_commission_holds_offer() -> None:
    engine = EvidenceFirstOfferIntelligence(
        qualification_policy=OfferQualificationPolicy(min_commission_rate=5.0)
    )
    decision = engine.qualify(
        engine.derive_features(offer(commission=1.0, extra=0.0), as_of=NOW),
        evaluated_at=NOW,
    )
    assert decision.state is OfferQualificationState.HOLD
    assert decision.recommended_action is OfferRecommendedAction.HOLD


def test_thin_buyer_confidence_watches_offer() -> None:
    engine = EvidenceFirstOfferIntelligence(
        qualification_policy=OfferQualificationPolicy(min_rating=4.5, min_review_count=50)
    )
    decision = engine.qualify(
        engine.derive_features(offer(rating=4.2, reviews=10), as_of=NOW),
        evaluated_at=NOW,
    )
    assert decision.state is OfferQualificationState.WATCH
    assert decision.recommended_action is OfferRecommendedAction.WATCH


def test_missing_session_context_is_explicit_unknown_but_does_not_fake_failure() -> None:
    features = EvidenceFirstOfferIntelligence().derive_features(
        offer(session_context_id=None),
        as_of=NOW,
    )
    assert "session_context" in features.unknown_features


@pytest.mark.parametrize(
    "factory",
    [
        lambda: OfferFeaturePolicy(version=" "),
        lambda: OfferFeaturePolicy(max_observation_age=timedelta(0)),
        lambda: OfferQualificationPolicy(version=" "),
        lambda: OfferQualificationPolicy(min_commission_rate=-1),
        lambda: OfferQualificationPolicy(min_rating=6),
        lambda: OfferQualificationPolicy(min_review_count=-1),
    ],
)
def test_invalid_policies_fail_fast(factory) -> None:
    with pytest.raises(ValueError):
        factory()
