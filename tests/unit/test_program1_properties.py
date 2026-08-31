import math
from datetime import UTC, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)


@given(
    sold=st.integers(min_value=0, max_value=10**12),
    rating=st.floats(min_value=0, max_value=5, allow_nan=False, allow_infinity=False),
    reviews=st.integers(min_value=0, max_value=10**12),
    price=st.one_of(st.none(), st.decimals(min_value=0, max_value=10**9, allow_nan=False)),
)
def test_score_is_always_finite_and_bounded(
    sold: int,
    rating: float,
    reviews: int,
    price: Decimal | None,
) -> None:
    observation = ProductObservation(
        observation_id="property-test",
        platform="shopee",
        shop_id="shop",
        item_id="item",
        collected_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name="Product",
        price_current=price,
        sold_signal=sold,
        rating=rating,
        review_count=reviews,
    )
    score = ProductIntelligenceEngine(ScoringPolicy()).score(observation).total_score
    assert math.isfinite(score)
    assert 0 <= score <= 100


@given(
    sold_a=st.integers(min_value=0, max_value=999),
    sold_b=st.integers(min_value=0, max_value=999),
)
def test_demand_component_is_monotonic_before_saturation(sold_a: int, sold_b: int) -> None:
    low, high = sorted((sold_a, sold_b))
    engine = ProductIntelligenceEngine(ScoringPolicy())

    def score(sold: int) -> float:
        observation = ProductObservation(
            observation_id=f"o-{sold}",
            platform="shopee",
            shop_id="shop",
            item_id=f"item-{sold}",
            collected_at=datetime(2026, 8, 31, tzinfo=UTC),
            product_name="Product",
            sold_signal=sold,
            rating=0,
            review_count=0,
        )
        return engine.score(observation).component_scores["demand"]

    assert score(low) <= score(high)
