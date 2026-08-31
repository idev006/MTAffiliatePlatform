from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.persistence.inmemory.affiliate_offer import (
    InMemoryAffiliateOfferRepository,
)
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)


def offer(
    observation_id: str,
    offer_id: str,
    *,
    commission: float,
    account: str = "affiliate-1",
    available: bool = True,
) -> AffiliateOfferObservation:
    return AffiliateOfferObservation(
        observation_id=observation_id,
        offer_id=offer_id,
        product_id="product-1",
        platform="shopee",
        shop_id=f"shop-{offer_id}",
        item_id=f"item-{offer_id}",
        affiliate_account_id=account,
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name=f"Product {offer_id}",
        commission_rate=commission,
        rating=4.5,
        review_count=100,
        sold_signal=500,
        available=available,
    )


def service() -> Program2Service:
    return Program2Service(
        InMemoryAffiliateOfferRepository(),
        AffiliateOfferEngine(OfferScoringPolicy()),
    )


def test_program2_ingest_rank_select_and_retrieve() -> None:
    app = service()
    observations = [
        offer("obs-1", "offer-high", commission=40),
        offer("obs-2", "offer-low", commission=5),
        offer("obs-3", "offer-disabled", commission=80, available=False),
    ]
    assert app.ingest_observations(observations) == 3
    ranked = app.rank_offers("product-1", affiliate_account_id="affiliate-1")
    assert [score.commercial_key[3] for score in ranked] == ["offer-high", "offer-low"]
    selection = app.select_offers(
        "product-1",
        affiliate_account_id="affiliate-1",
        backup_count=1,
        now=datetime(2026, 8, 31, tzinfo=UTC),
    )
    assert selection.preferred_offer_id == "offer-high"
    assert selection.backup_offer_ids == ["offer-low"]
    assert app.repository.get_selection(selection.selection_id) == selection


def test_program2_idempotent_observation_and_collision_detection() -> None:
    app = service()
    original = offer("obs-1", "offer-1", commission=10)
    assert app.ingest_observations([original]) == 1
    assert app.ingest_observations([original]) == 0
    changed = original.model_copy(update={"offer_id": "different"})
    with pytest.raises(ValueError, match="collision"):
        app.ingest_observations([changed])


def test_program2_account_context_isolation_and_no_offer_failure() -> None:
    app = service()
    app.ingest_observations(
        [
            offer("obs-a", "offer-a", commission=20, account="account-a"),
            offer("obs-b", "offer-b", commission=30, account="account-b"),
        ]
    )
    ranked = app.rank_offers("product-1", affiliate_account_id="account-a")
    assert [score.commercial_key[4] for score in ranked] == ["account-a"]
    with pytest.raises(ValueError, match="no eligible"):
        app.select_offers("missing", affiliate_account_id="account-a")
    with pytest.raises(ValueError, match="backup_count"):
        app.select_offers(
            "product-1",
            affiliate_account_id="account-a",
            backup_count=-1,
        )
