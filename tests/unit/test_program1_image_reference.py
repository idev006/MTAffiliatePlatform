import hashlib
import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.domain.product.models import ProductObservation


def item(**extra):
    return ProductObservation(
        observation_id="image-test",
        platform="shopee",
        shop_id="s",
        item_id="i",
        product_name="Product",
        collected_at=datetime(2026, 9, 9, tzinfo=UTC),
        **extra,
    )


def test_legacy_fingerprint_is_unchanged():
    original = item().model_dump(mode="json")
    original.pop("primary_image_url")
    legacy = hashlib.sha256(
        json.dumps([original], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert Program1Service._batch_fingerprint([item()]) == legacy
    assert Program1Service._batch_fingerprint([item(primary_image_url=None)]) == legacy
    assert (
        Program1Service._batch_fingerprint(
            [item(primary_image_url="https://example.test/image.jpg")]
        )
        != legacy
    )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.test/a",
        "//example.test/a",
        "javascript:alert(1)",
        "https://u:p@example.test/a",
        "https:///a",
        "https://example.test:bad/a",
        "https://[invalid/a",
        "https://example.test/a b",
        "https://example.test\\a",
    ],
)
def test_invalid_image_reference_is_rejected(url):
    with pytest.raises(ValidationError):
        item(primary_image_url=url)


@pytest.mark.parametrize("url", [None, "http://example.test/a", "https://example.test/a?size=2"])
def test_image_reference_is_optional_and_preserved(url):
    assert item(primary_image_url=url).primary_image_url == url
