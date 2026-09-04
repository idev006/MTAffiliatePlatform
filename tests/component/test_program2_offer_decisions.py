from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.inmemory.affiliate_offer import (
    InMemoryAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_decision import (
    InMemoryProgram2DecisionRepository,
)
from mtaffiliate.application.program2_intelligence import (
    OfferSelectionPolicy,
    Program2OfferDecisionService,
)
from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.engines.affiliate_offer_engine.service import EvidenceFirstOfferIntelligence

NOW = datetime(2026, 9, 4, 16, 30, tzinfo=UTC)
PRODUCT_ID = "shopee:shop-1:item-1"


def obs(
    observation_id: str,
    offer_id: str,
    *,
    commission: float,
    rating: float,
    reviews: int,
    sold: int,
    job_id: str = "job-1",
    account_id: str = "account-1",
    available: bool = True,
    observed_at: datetime = NOW,
) -> AffiliateOfferObservation:
    return AffiliateOfferObservation(
        observation_id=observation_id,
        offer_id=offer_id,
        product_id=PRODUCT_ID,
        platform="shopee",
        shop_id=f"shop-{offer_id}",
        item_id="item-1",
        affiliate_account_id=account_id,
        session_context_id="session-1",
        source_worker_id="worker-1",
        source_job_id=job_id,
        extractor_version="fixture-v1",
        observed_at=observed_at,
        seller_name=f"Seller {offer_id}",
        product_name="Synthetic SSD",
        price_current=Decimal(1590),
        commission_rate=commission,
        extra_commission_rate=0,
        rating=rating,
        review_count=reviews,
        sold_signal=sold,
        available=available,
    )


def build(backup_count: int = 2):
    offers = InMemoryAffiliateOfferRepository()
    decisions = InMemoryProgram2DecisionRepository()
    service = Program2OfferDecisionService(
        offers=offers,
        decisions=decisions,
        intelligence=EvidenceFirstOfferIntelligence(),
        selection_policy=OfferSelectionPolicy(backup_count=backup_count),
    )
    return offers, decisions, service


def test_selection_is_deterministic_and_persists_preferred_backups() -> None:
    offers, decisions, service = build(backup_count=2)
    offers.add_observations(
        [
            obs("obs-a", "offer-a", commission=8, rating=4.9, reviews=500, sold=1000),
            obs("obs-b", "offer-b", commission=12, rating=4.6, reviews=100, sold=200),
            obs("obs-c", "offer-c", commission=10, rating=4.8, reviews=300, sold=500),
        ]
    )

    decision = service.evaluate_and_select(
        product_id=PRODUCT_ID,
        affiliate_account_id="account-1",
        source_job_id="job-1",
        evaluated_at=NOW,
    )

    assert decision.preferred_offer_id == "offer-b"
    assert decision.backup_offer_ids == ("offer-c", "offer-a")
    assert decisions.get(decision.decision_id) == decision
    assert decisions.latest_for_product_account(PRODUCT_ID, "account-1") == decision
    assert set(decision.evidence_refs) == {"obs-a", "obs-b", "obs-c"}


def test_same_inputs_and_timestamp_produce_same_decision_identity() -> None:
    offers, decisions, service = build()
    offers.add_observations(
        [obs("obs-a", "offer-a", commission=12, rating=4.8, reviews=100, sold=200)]
    )

    first = service.evaluate_and_select(
        product_id=PRODUCT_ID,
        affiliate_account_id="account-1",
        source_job_id="job-1",
        evaluated_at=NOW,
    )
    replay = service.evaluate_and_select(
        product_id=PRODUCT_ID,
        affiliate_account_id="account-1",
        source_job_id="job-1",
        evaluated_at=NOW,
    )

    assert replay == first
    assert decisions.get(first.decision_id) == first


def test_other_job_or_account_observations_do_not_contaminate_selection() -> None:
    offers, _decisions, service = build()
    offers.add_observations(
        [
            obs("obs-current", "offer-current", commission=8, rating=4.8, reviews=100, sold=100),
            obs(
                "obs-old-job",
                "offer-old",
                commission=99,
                rating=5,
                reviews=999,
                sold=9999,
                job_id="job-old",
            ),
            obs(
                "obs-other-account",
                "offer-other",
                commission=99,
                rating=5,
                reviews=999,
                sold=9999,
                account_id="account-2",
            ),
        ]
    )

    decision = service.evaluate_and_select(
        product_id=PRODUCT_ID,
        affiliate_account_id="account-1",
        source_job_id="job-1",
        evaluated_at=NOW,
    )

    assert decision.preferred_offer_id == "offer-current"
    assert decision.evidence_refs == ("obs-current",)


def test_unqualified_candidates_fail_closed() -> None:
    offers, _decisions, service = build()
    offers.add_observations(
        [
            obs(
                "obs-stale",
                "offer-stale",
                commission=20,
                rating=4.9,
                reviews=1000,
                sold=5000,
                observed_at=NOW - timedelta(days=2),
            ),
            obs(
                "obs-unavailable",
                "offer-unavailable",
                commission=50,
                rating=5,
                reviews=1000,
                sold=5000,
                available=False,
            ),
        ]
    )

    with pytest.raises(ValueError, match="no qualified affiliate offers"):
        service.evaluate_and_select(
            product_id=PRODUCT_ID,
            affiliate_account_id="account-1",
            source_job_id="job-1",
            evaluated_at=NOW,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("product_id", " ", "product_id"),
        ("affiliate_account_id", " ", "affiliate_account_id"),
        ("source_job_id", " ", "source_job_id"),
    ],
)
def test_required_selection_scope_is_validated(field: str, value: str, message: str) -> None:
    _offers, _decisions, service = build()
    kwargs = {
        "product_id": PRODUCT_ID,
        "affiliate_account_id": "account-1",
        "source_job_id": "job-1",
        "evaluated_at": NOW,
    }
    kwargs[field] = value
    with pytest.raises(ValueError, match=message):
        service.evaluate_and_select(**kwargs)


def test_selection_policy_validates_configuration() -> None:
    with pytest.raises(ValueError):
        OfferSelectionPolicy(version=" ")
    with pytest.raises(ValueError):
        OfferSelectionPolicy(backup_count=-1)
