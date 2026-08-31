from datetime import UTC, datetime
from decimal import Decimal

from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)


def test_ingest_to_shortlist_thin_slice() -> None:
    service = Program1Service(
        InMemoryProductRepository(),
        ProductIntelligenceEngine(ScoringPolicy()),
        shortlist_limit=20,
        minimum_score=0,
    )
    item = ProductObservation(
        observation_id="obs-1",
        platform="shopee",
        shop_id="s1",
        item_id="i1",
        collected_at=datetime.now(UTC),
        product_name="Fixture product",
        price_current=Decimal(299),
        sold_signal=100,
        rating=4.8,
        review_count=50,
    )
    first = service.ingest([item])
    second = service.ingest([item])
    assert first.accepted_count == 1
    assert second.accepted_count == 0
    assert service.build_shortlist()[0].product_key == ("shopee", "s1", "i1")
