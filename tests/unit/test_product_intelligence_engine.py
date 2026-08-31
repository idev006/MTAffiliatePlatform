from datetime import UTC, datetime
from decimal import Decimal

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)


def observation(item_id: str, sold: int, rating: float, reviews: int) -> ProductObservation:
    return ProductObservation(
        observation_id=f"obs-{item_id}",
        platform="shopee",
        shop_id="shop-1",
        item_id=item_id,
        collected_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name=f"Product {item_id}",
        price_current=Decimal("299.00"),
        sold_signal=sold,
        rating=rating,
        review_count=reviews,
    )


def test_shortlist_is_deterministic_and_ranked() -> None:
    engine = ProductIntelligenceEngine(ScoringPolicy())
    result = engine.shortlist(
        [observation("low", 10, 3.0, 10), observation("high", 1000, 5.0, 500)],
        limit=10,
    )
    assert [entry.product_key[2] for entry in result] == ["high", "low"]
    assert [entry.rank for entry in result] == [1, 2]
