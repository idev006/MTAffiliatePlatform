from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from mtaffiliate.interfaces.api.app import create_app

NOW = datetime(2026, 8, 31, tzinfo=UTC).isoformat()


def offer_payload(observation_id: str = "obs-1", offer_id: str = "offer-1") -> dict:
    return {
        "observation_id": observation_id,
        "offer_id": offer_id,
        "product_id": "product-1",
        "platform": "shopee",
        "shop_id": "shop-1",
        "item_id": "item-1",
        "affiliate_account_id": "affiliate-1",
        "observed_at": NOW,
        "product_name": "Product",
        "commission_rate": 20,
        "rating": 4.5,
        "review_count": 100,
        "sold_signal": 500,
        "available": True,
    }


def publish_plan_payload(video_id: str = "video-1", sha: str | None = None) -> dict:
    return {
        "publish_job_id": "job-1",
        "platform": "shopee",
        "target_account_id": "target-1",
        "video_id": video_id,
        "video_sha256": sha or "a" * 64,
        "offers": [
            {
                "selection_id": "sel-1",
                "product_id": "product-1",
                "offer_id": "offer-1",
                "shop_id": "shop-1",
                "item_id": "item-1",
                "affiliate_account_id": "affiliate-1",
                "affiliate_link_id": "link-1",
            }
        ],
        "duplicate_policy_version": "duplicate-v1",
        "plan_version": "plan-v1",
        "created_at": NOW,
    }


def test_program2_http_ingest_rank_and_select() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/program2/observations",
        json={"observations": [offer_payload()]},
    )
    assert response.status_code == 200
    assert response.json() == {"received_count": 1, "accepted_count": 1}

    ranking = client.get(
        "/api/v1/program2/products/product-1/offers",
        params={"affiliate_account_id": "affiliate-1"},
    )
    assert ranking.status_code == 200
    assert ranking.json()[0]["commercial_key"][3] == "offer-1"

    selection = client.post(
        "/api/v1/program2/products/product-1/selection",
        json={"affiliate_account_id": "affiliate-1", "backup_count": 0},
    )
    assert selection.status_code == 200
    assert selection.json()["preferred_offer_id"] == "offer-1"


def test_program2_collision_and_no_offer_are_409() -> None:
    client = TestClient(create_app())
    original = offer_payload()
    assert client.post(
        "/api/v1/program2/observations",
        json={"observations": [original]},
    ).status_code == 200
    changed = offer_payload(offer_id="changed")
    conflict = client.post(
        "/api/v1/program2/observations",
        json={"observations": [changed]},
    )
    assert conflict.status_code == 409

    missing = client.post(
        "/api/v1/program2/products/missing/selection",
        json={"affiliate_account_id": "affiliate-1"},
    )
    assert missing.status_code == 409


def test_program3_http_duplicate_and_unknown_outcome_guards() -> None:
    client = TestClient(create_app())
    plan = publish_plan_payload()
    allowed = client.post("/api/v1/program3/publish/evaluate", json=plan)
    assert allowed.status_code == 200
    assert allowed.json()["allowed"] is True

    status = client.post(
        "/api/v1/program3/publish/status",
        json={"plan": plan, "status": "PUBLISHED"},
    )
    assert status.status_code == 200
    blocked = client.post("/api/v1/program3/publish/evaluate", json=plan)
    assert blocked.json()["reason"] == "VIDEO_ALREADY_PUBLISHED_TO_PLATFORM"

    other = publish_plan_payload(video_id="video-2", sha="b" * 64)
    client.post(
        "/api/v1/program3/publish/status",
        json={"plan": other, "status": "POST_OUTCOME_UNKNOWN"},
    )
    ambiguous = client.post("/api/v1/program3/publish/evaluate", json=other)
    assert ambiguous.json()["reason"] == "PUBLISH_OUTCOME_REQUIRES_RECONCILIATION"


def test_program2_program3_validation_errors_are_422() -> None:
    client = TestClient(create_app())
    invalid_offer = client.post(
        "/api/v1/program2/observations",
        json={"observations": [{"observation_id": ""}]},
    )
    assert invalid_offer.status_code == 422

    invalid_plan = publish_plan_payload()
    invalid_plan["video_sha256"] = "short"
    response = client.post("/api/v1/program3/publish/evaluate", json=invalid_plan)
    assert response.status_code == 422
