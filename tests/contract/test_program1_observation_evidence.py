from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.interfaces.api.app import build_inmemory_program1, create_app


def test_evidence_is_stored_history_newest_first_and_bounded() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program1"}))
    endpoint = "/api/v1/program1/products/shopee/shop/item/observations"
    assert client.get(endpoint).json() == []
    for number in range(3):
        result = client.post(
            "/api/v1/program1/observations",
            json={
                "batch_id": f"image-evidence-{number}",
                "observations": [
                    {
                        "observation_id": f"image-{number}",
                        "platform": "shopee",
                        "shop_id": "shop",
                        "item_id": "item",
                        "product_name": "Evidence",
                        "collected_at": datetime(2026, 9, 9, number, tzinfo=UTC).isoformat(),
                        "product_url": "https://example.test/product",
                        "primary_image_url": f"https://example.test/image-{number}.jpg",
                    }
                ],
            },
        )
        assert result.status_code == 200
    response = client.get(endpoint, params={"limit": 2})
    assert response.status_code == 200
    assert [row["observation_id"] for row in response.json()] == ["image-2", "image-1"]
    assert response.json()[0]["primary_image_url"] == "https://example.test/image-2.jpg"
    assert client.get(endpoint.replace("/item/", "/missing/")).json() == []
    for limit in (0, 101):
        assert client.get(endpoint, params={"limit": limit}).status_code == 422
        with pytest.raises(ValueError, match="limit"):
            build_inmemory_program1(Settings()).observation_evidence(
                ("shopee", "shop", "item"), limit=limit
            )


def test_program1_evidence_route_is_not_exposed_in_program2_runtime() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program2"}))
    assert client.get("/api/v1/program1/products/shopee/shop/item/observations").status_code == 404


def test_product_evidence_page_is_ordered_bounded_and_latest() -> None:
    service = build_inmemory_program1(Settings())
    from mtaffiliate.domain.product.models import ProductObservation

    for hour, (oid, item_id) in enumerate([("older", "b"), ("a", "a"), ("newer", "b")]):
        service.ingest(
            [
                ProductObservation(
                    observation_id=oid,
                    platform="shopee",
                    shop_id="s",
                    item_id=item_id,
                    product_name=oid,
                    collected_at=datetime(2026, 9, 9, hour, tzinfo=UTC),
                )
            ]
        )
    client = TestClient(create_app(Settings(), program1=service, enabled_programs={"program1"}))
    result = client.get("/api/v1/program1/products?limit=1&offset=0").json()
    assert result["total"] == 2
    assert result["items"][0]["item_id"] == "a"
    assert (
        client.get("/api/v1/program1/products?limit=1&offset=1").json()["items"][0][
            "observation_id"
        ]
        == "newer"
    )
    assert client.get("/api/v1/program1/products?offset=100").json()["items"] == []
    for query in ["limit=0", "limit=101", "offset=-1"]:
        assert client.get("/api/v1/program1/products?" + query).status_code == 422
    for limit, offset in [(0, 0), (101, 0), (1, -1)]:
        with pytest.raises(ValueError):
            service.product_evidence_page(limit=limit, offset=offset)
