from __future__ import annotations

from datetime import UTC, datetime

from mtaffiliate.domain.affiliate_offer.artifacts import AffiliateLink
from mtaffiliate.domain.affiliate_offer.models import OfferSelection
from mtaffiliate.engines.affiliate_offer_engine.link_validation import (
    AffiliateLinkValidationEngine,
)

NOW = datetime(2026, 8, 31, tzinfo=UTC)


def selection() -> OfferSelection:
    return OfferSelection(
        selection_id="sel-1",
        product_id="product-1",
        preferred_offer_id="offer-1",
        backup_offer_ids=["offer-2"],
        affiliate_account_id="account-1",
        selected_at=NOW,
        model_version="program2-offer-scoring-framework-v0",
    )


def link(**updates) -> AffiliateLink:
    data = {
        "affiliate_link_id": "link-1",
        "product_id": "product-1",
        "offer_id": "offer-1",
        "affiliate_account_id": "account-1",
        "url": "https://shopee.co.th/example",
        "acquired_at": NOW,
    }
    data.update(updates)
    return AffiliateLink(**data)


def test_link_matching_selection_is_valid() -> None:
    result = AffiliateLinkValidationEngine().validate_selected_link(selection(), link())
    assert result.valid


def test_link_must_match_product_account_and_selected_offer() -> None:
    engine = AffiliateLinkValidationEngine()
    assert engine.validate_selected_link(
        selection(), link(product_id="wrong")
    ).reason == "PRODUCT_ID_MISMATCH"
    assert engine.validate_selected_link(
        selection(), link(affiliate_account_id="wrong")
    ).reason == "AFFILIATE_ACCOUNT_MISMATCH"
    assert engine.validate_selected_link(
        selection(), link(offer_id="wrong")
    ).reason == "OFFER_NOT_IN_SELECTION"


def test_backup_offer_link_is_also_valid_handoff_candidate() -> None:
    result = AffiliateLinkValidationEngine().validate_selected_link(
        selection(),
        link(offer_id="offer-2"),
    )
    assert result.valid
