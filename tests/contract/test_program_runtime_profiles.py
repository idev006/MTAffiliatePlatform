from __future__ import annotations

from fastapi.testclient import TestClient

from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.interfaces.api.app import create_app
from mtaffiliate.interfaces.cli import run_api


def test_program1_profile_exposes_only_program1_routes() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program1"}))

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["enabled_programs"] == ["program1"]
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/program1/shortlist").status_code == 200
    assert client.post("/api/v1/program2/observations", json={"observations": []}).status_code == 404
    assert client.post("/api/v1/program3/publish/evaluate", json={}).status_code == 404


def test_program2_profile_exposes_only_program2_routes() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program2"}))

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/program1/shortlist").status_code == 404
    assert client.post("/api/v1/program2/observations", json={"observations": []}).status_code == 200
    assert client.post("/api/v1/program3/publish/evaluate", json={}).status_code == 404


def test_program3_profile_exposes_only_program3_routes() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program3"}))

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/program1/shortlist").status_code == 404
    assert client.post("/api/v1/program2/observations", json={"observations": []}).status_code == 404
    assert client.post("/api/v1/program3/publish/evaluate", json={}).status_code == 422


def test_unknown_program_profile_fails_closed() -> None:
    try:
        create_app(Settings(), enabled_programs={"program4"})
    except ValueError as exc:
        assert "program4" in str(exc)
    else:
        raise AssertionError("unknown program should fail closed")


def test_api_console_scripts_dispatch_to_expected_runtime(monkeypatch) -> None:
    calls: list[tuple[str, str, int]] = []

    def fake_run(module_path: str, *, host: str, port: int) -> None:
        calls.append((module_path, host, port))

    monkeypatch.setattr(run_api.uvicorn, "run", fake_run)
    monkeypatch.setenv("MTAFFILIATE_HOST", "0.0.0.0")
    monkeypatch.setenv("MTAFFILIATE_PORT", "8011")

    run_api.main_program1()
    run_api.main_program2()
    run_api.main_program3()
    run_api.main_all()

    assert calls == [
        ("mtaffiliate.runtime.program1:app", "0.0.0.0", 8011),
        ("mtaffiliate.runtime.program2:app", "0.0.0.0", 8011),
        ("mtaffiliate.runtime.program3:app", "0.0.0.0", 8011),
        ("mtaffiliate.runtime.all:app", "0.0.0.0", 8011),
    ]
