from __future__ import annotations

from mtaffiliate.domain.affiliate_offer.artifacts import (
    AffiliateLink,
    LinkValidationResult,
)
from mtaffiliate.domain.affiliate_offer.models import OfferSelection


class AffiliateLinkValidationEngine:
    """Pure validation of Program 2 output before Program 3 handoff."""

    def validate_selected_link(
        self,
        selection: OfferSelection,
        link: AffiliateLink,
    ) -> LinkValidationResult:
        if link.product_id != selection.product_id:
            return LinkValidationResult(valid=False, reason="PRODUCT_ID_MISMATCH")
        if link.affiliate_account_id != selection.affiliate_account_id:
            return LinkValidationResult(valid=False, reason="AFFILIATE_ACCOUNT_MISMATCH")
        selected_offer_ids = {
            selection.preferred_offer_id,
            *selection.backup_offer_ids,
        }
        if link.offer_id not in selected_offer_ids:
            return LinkValidationResult(valid=False, reason="OFFER_NOT_IN_SELECTION")
        return LinkValidationResult(valid=True, reason="LINK_MATCHES_SELECTION")
