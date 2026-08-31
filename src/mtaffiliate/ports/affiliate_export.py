from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.affiliate_offer.artifacts import AffiliateLink, OfferExportArtifact


class OfferExportParserPort(Protocol):
    def parse(
        self,
        artifact: OfferExportArtifact,
        raw_content: bytes,
    ) -> list[AffiliateLink]: ...
