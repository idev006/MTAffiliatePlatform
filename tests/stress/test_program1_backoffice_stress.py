from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)

pytestmark = pytest.mark.stress


def make_observation(index: int) -> ProductObservation:
    return ProductObservation(
        observation_id=f"obs-{index}",
        platform="shopee",
        shop_id=f"shop-{index // 1000}",
        item_id=f"item-{index}",
        collected_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
        product_name=f"Product {index}",
        price_current=Decimal(index % 10_000),
        sold_signal=index % 2_000,
        rating=(index % 50) / 10,
        review_count=index % 1_000,
    )


def test_ingest_and_shortlist_100k_observations() -> None:
    repository = InMemoryProductRepository()
    observations = [make_observation(index) for index in range(100_000)]
    assert repository.add_observations(observations) == 100_000

    service = Program1Service(
        repository,
        ProductIntelligenceEngine(ScoringPolicy()),
        shortlist_limit=20,
        minimum_score=0,
    )
    shortlist = service.build_shortlist()
    assert len(shortlist) == 20
    assert shortlist[0].rank == 1
    assert shortlist[-1].rank == 20
