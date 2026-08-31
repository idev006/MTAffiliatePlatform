from __future__ import annotations

import json

from mtaffiliate.domain.affiliate_offer.artifacts import AffiliateLink, OfferExportArtifact


class SyntheticJsonOfferExportParser:
    """Laboratory parser for contract/golden-fixture testing only.

    It intentionally does not claim compatibility with any real Shopee export.
    """

    def parse(
        self,
        artifact: OfferExportArtifact,
        raw_content: bytes,
    ) -> list[AffiliateLink]:
        if artifact.format != "synthetic-json-v1":
            raise ValueError("unsupported synthetic parser format")
        try:
            payload = json.loads(raw_content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid export artifact content") from exc
        if not isinstance(payload, list):
            raise TypeError("export artifact root must be a list")
        links = [AffiliateLink.model_validate(item) for item in payload]
        if any(link.affiliate_account_id != artifact.affiliate_account_id for link in links):
            raise ValueError("export artifact contains cross-account link data")
        return links
