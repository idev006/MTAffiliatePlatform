from datetime import timedelta

from fastapi.testclient import TestClient

from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
    InMemoryWorkerRegistryRepository,
)
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.interfaces.api.app import create_app


def registration(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "worker_id": "worker-01",
        "worker_type": "DISCOVERY_BROWSER_WORKER",
        "installation_id": "install-1",
        "version": "0.1.9",
        "capabilities": ["collector:shopee-current-page-lab-v2"],
    }
    values.update(overrides)
    return values


def test_register_then_heartbeat_then_read_contract() -> None:
    client = TestClient(create_app(Settings()))

    registered = client.post("/api/v1/workers/register", json=registration())
    assert registered.status_code == 200
    body = registered.json()
    assert body["worker_id"] == "worker-01"
    assert body["worker_type"] == "DISCOVERY_BROWSER_WORKER"
    assert body["health_state"] == "ONLINE_IDLE"
    assert body["version_no"] == 1
    assert "enrolled_at" in body
    assert "last_seen_at" in body

    beaten = client.post(
        "/api/v1/workers/worker-01/heartbeat",
        json={"health_state": "ONLINE_BUSY", "schema_version": "worker-heartbeat-v1"},
    )
    assert beaten.status_code == 200
    assert beaten.json()["health_state"] == "ONLINE_BUSY"
    assert beaten.json()["version_no"] == 2

    listed = client.get("/api/v1/workers")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["worker_id"] == "worker-01"
    assert listed.json()[0]["health_state"] == "ONLINE_BUSY"

    fetched = client.get("/api/v1/workers/worker-01")
    assert fetched.status_code == 200
    assert fetched.json()["worker_id"] == "worker-01"
    assert fetched.json()["stale"] is False


def test_register_is_idempotent_for_same_installation() -> None:
    client = TestClient(create_app(Settings()))
    first = client.post("/api/v1/workers/register", json=registration())
    second = client.post("/api/v1/workers/register", json=registration())
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["version_no"] == 2
    assert second.json()["worker_id"] == first.json()["worker_id"]


def test_register_conflicts_for_different_installation() -> None:
    client = TestClient(create_app(Settings()))
    assert client.post("/api/v1/workers/register", json=registration()).status_code == 200
    conflict = client.post(
        "/api/v1/workers/register",
        json=registration(installation_id="other-install"),
    )
    assert conflict.status_code == 409
    assert "worker_id collision" in conflict.json()["detail"]


def test_heartbeat_for_unknown_worker_returns_404() -> None:
    client = TestClient(create_app(Settings()))
    response = client.post(
        "/api/v1/workers/ghost/heartbeat",
        json={"health_state": "ONLINE_IDLE"},
    )
    assert response.status_code == 404
    assert "unknown worker" in response.json()["detail"]


def test_heartbeat_rejects_back_office_only_states_with_422() -> None:
    client = TestClient(create_app(Settings()))
    assert client.post("/api/v1/workers/register", json=registration()).status_code == 200
    for state in ("OFFLINE", "DISABLED"):
        response = client.post(
            "/api/v1/workers/worker-01/heartbeat",
            json={"health_state": state},
        )
        assert response.status_code == 422
        assert "may only report" in response.json()["detail"]


def test_registry_endpoints_reject_invalid_payloads_with_422() -> None:
    client = TestClient(create_app(Settings()))
    cases = [
        {**registration(), "worker_id": "   "},
        {**registration(), "worker_type": "ROBOT_WORKER"},
        {**registration(), "installation_id": ""},
        {**registration(), "version": ""},
    ]
    for payload in cases:
        response = client.post("/api/v1/workers/register", json=payload)
        assert response.status_code == 422


def test_get_worker_returns_404_for_unknown_worker() -> None:
    client = TestClient(create_app(Settings()))
    response = client.get("/api/v1/workers/missing")
    assert response.status_code == 404
    assert "unknown worker" in response.json()["detail"]


def test_list_derives_offline_for_stale_worker() -> None:
    registry = WorkerRegistryService(
        InMemoryWorkerRegistryRepository(),
        stale_after=timedelta(microseconds=1),
    )
    client = TestClient(create_app(Settings(), registry=registry))

    assert client.post("/api/v1/workers/register", json=registration()).status_code == 200

    listed = client.get("/api/v1/workers")
    assert listed.status_code == 200
    entry = listed.json()[0]
    assert entry["health_state"] == "OFFLINE"
    assert entry["stale"] is True
