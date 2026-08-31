from datetime import datetime, timezone

from fastapi.testclient import TestClient

from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.interfaces.api.app import create_app


def observation(observation_id: str = "o1", item_id: str = "i1") -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "platform": "shopee",
        "shop_id": "s1",
        "item_id": item_id,
        "collected_at": datetime(2026, 8, 31, tzinfo=timezone.utc).isoformat(),
        "product_name": "Product",
        "price_current": "100.00",
        "sold_signal": 100,
        "rating": 4.5,
        "review_count": 20,
    }


def test_health_endpoint() -> None:
    client = TestClient(create_app(Settings()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_then_shortlist_contract() -> None:
    client = TestClient(create_app(Settings(program1={"shortlist_limit": 5})))
    response = client.post(
        "/api/v1/program1/observations",
        json={"batch_id": "batch-1", "observations": [observation()]},
    )
    assert response.status_code == 200
    assert response.json() == {
        "batch_id": "batch-1",
        "received_count": 1,
        "accepted_count": 1,
    }

    shortlist = client.get("/api/v1/program1/shortlist")
    assert shortlist.status_code == 200
    assert len(shortlist.json()) == 1
    assert shortlist.json()[0]["product_key"] == ["shopee", "s1", "i1"]


def test_same_batch_retry_returns_same_ack() -> None:
    client = TestClient(create_app(Settings()))
    payload = {"batch_id": "batch-1", "observations": [observation()]}
    first = client.post("/api/v1/program1/observations", json=payload)
    retry = client.post("/api/v1/program1/observations", json=payload)
    assert first.status_code == 200
    assert retry.status_code == 200
    assert retry.json() == first.json()
    assert retry.json()["accepted_count"] == 1


def test_reusing_batch_id_with_different_payload_returns_409() -> None:
    client = TestClient(create_app(Settings()))
    assert client.post(
        "/api/v1/program1/observations",
        json={"batch_id": "batch-1", "observations": [observation("o1", "A")]},
    ).status_code == 200
    conflict = client.post(
        "/api/v1/program1/observations",
        json={"batch_id": "batch-1", "observations": [observation("o2", "B")]},
    )
    assert conflict.status_code == 409


def test_observation_id_collision_returns_409() -> None:
    client = TestClient(create_app(Settings()))
    assert client.post(
        "/api/v1/program1/observations",
        json={"batch_id": "batch-1", "observations": [observation("same", "A")]},
    ).status_code == 200
    conflict = client.post(
        "/api/v1/program1/observations",
        json={"batch_id": "batch-2", "observations": [observation("same", "B")]},
    )
    assert conflict.status_code == 409


def test_invalid_payloads_return_422_not_500() -> None:
    client = TestClient(create_app(Settings()))
    cases = [
        {"batch_id": "", "observations": []},
        {"batch_id": "b", "observations": [{**observation(), "rating": 9}]},
        {"batch_id": "b", "observations": [{**observation(), "price_current": "-1"}]},
        {"batch_id": "b", "observations": [{**observation(), "product_name": "   "}]},
    ]
    for payload in cases:
        response = client.post("/api/v1/program1/observations", json=payload)
        assert response.status_code == 422
