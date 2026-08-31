from datetime import UTC, datetime

import pytest

from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)


def offer(**overrides) -> AffiliateOfferObservation:
    data = {
        "observation_id": "obs-1",
        "offer_id": "offer-1",
        "product_id": "product-1",
        "platform": "shopee",
        "shop_id": "shop-1",
        "item_id": "item-1",
        "affiliate_account_id": "affiliate-1",
        "observed_at": datetime(2026, 8, 31, tzinfo=UTC),
        "product_name": "Product",
        "commission_rate": 12.0,
        "extra_commission_rate": 3.0,
        "rating": 4.5,
        "review_count": 250,
        "sold_signal": 800,
        "available": True,
    }
    data.update(overrides)
    return AffiliateOfferObservation(**data)


def test_eligible_offer_is_scored_with_stable_identity() -> None:
    engine = AffiliateOfferEngine(OfferScoringPolicy())
    score = engine.score(offer())
    assert score.commercial_key == (
        "shopee",
        "shop-1",
        "item-1",
        "offer-1",
        "affiliate-1",
    )
    assert 0 <= score.total_score <= 100


def test_unavailable_or_commissionless_offer_is_ineligible() -> None:
    engine = AffiliateOfferEngine(OfferScoringPolicy())
    assert not engine.is_eligible(offer(available=False))
    assert not engine.is_eligible(
        offer(commission_rate=None, extra_commission_rate=None)
    )


def test_rank_excludes_ineligible_and_orders_score_descending() -> None:
    engine = AffiliateOfferEngine(OfferScoringPolicy())
    high = offer(offer_id="high", commission_rate=50, rating=5, sold_signal=1000)
    low = offer(offer_id="low", commission_rate=1, rating=1, sold_signal=1)
    disabled = offer(offer_id="disabled", available=False)
    ranked = engine.rank([low, disabled, high])
    assert [item.commercial_key[3] for item in ranked] == ["high", "low"]


def test_policy_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError):
        OfferScoringPolicy(commission_weight=-1)
    with pytest.raises(ValueError):
        OfferScoringPolicy(
            commission_weight=0,
            rating_weight=0,
            review_weight=0,
            demand_weight=0,
        )
