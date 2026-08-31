from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.affiliate_export.synthetic_json import SyntheticJsonOfferExportParser
from mtaffiliate.domain.affiliate_offer.artifacts import OfferExportArtifact

NOW = datetime(2026, 8, 31, tzinfo=UTC)


def artifact(
    raw: bytes,
    *,
    account: str = "account-1",
    format_name: str = "synthetic-json-v1",
) -> OfferExportArtifact:
    return OfferExportArtifact(
        artifact_id="artifact-1",
        affiliate_account_id=account,
        generated_at=NOW,
        format=format_name,
        sha256=hashlib.sha256(raw).hexdigest(),
        source_job_id="job-1",
        parser_profile_version="synthetic-parser-v1",
    )


def raw_link(*, account: str = "account-1") -> bytes:
    return json.dumps(
        [
            {
                "affiliate_link_id": "link-1",
                "product_id": "product-1",
                "offer_id": "offer-1",
                "affiliate_account_id": account,
                "url": "https://shopee.co.th/example",
                "acquired_at": NOW.isoformat(),
                "source_artifact_id": "artifact-1",
            }
        ]
    ).encode()


def test_synthetic_parser_proves_parser_port_and_fixture_shape() -> None:
    raw = raw_link()
    links = SyntheticJsonOfferExportParser().parse(artifact(raw), raw)
    assert len(links) == 1
    assert links[0].offer_id == "offer-1"


def test_synthetic_parser_rejects_invalid_json() -> None:
    raw = b"not-json"
    with pytest.raises(ValueError):
        SyntheticJsonOfferExportParser().parse(artifact(raw), raw)


def test_synthetic_parser_rejects_non_list_root() -> None:
    raw = b'{"not":"a-list"}'
    with pytest.raises(TypeError):
        SyntheticJsonOfferExportParser().parse(artifact(raw), raw)


def test_synthetic_parser_rejects_cross_account_data() -> None:
    raw = raw_link(account="other")
    with pytest.raises(ValueError, match="cross-account"):
        SyntheticJsonOfferExportParser().parse(artifact(raw), raw)


def test_synthetic_parser_never_claims_unknown_real_format() -> None:
    raw = raw_link()
    with pytest.raises(ValueError, match="unsupported"):
        SyntheticJsonOfferExportParser().parse(
            artifact(raw, format_name="unknown-real-format"),
            raw,
        )
