from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mtaffiliate.runtime._factory import create_runtime_app

pytestmark = pytest.mark.integration


def write_runtime_config(root: Path, profile: str, database_name: str) -> None:
    source_root = Path(__file__).resolve().parents[3]
    config = root / "config"
    config.mkdir()
    shutil.copytree(source_root / "migrations", root / "migrations")
    (root / "alembic.ini").write_text(
        (source_root / "alembic.ini").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (config / "default.toml").write_text(
        """
[app]
name = "MTAffiliatePlatform"

[program1]
shortlist_limit = 5
minimum_score = 0.0
""",
        encoding="utf-8",
    )
    (config / f"{profile}.toml").write_text(
        f"""
[database]
url = "sqlite:///data/{database_name}"
auto_migrate = true
""",
        encoding="utf-8",
    )


def test_runtime_factory_uses_program_specific_profile(tmp_path: Path) -> None:
    write_runtime_config(tmp_path, "program1", "program1.db")

    app = create_runtime_app({"program1"}, default_profile="program1", project_root=tmp_path)
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/program1/shortlist").status_code == 200
    assert client.post("/api/v1/program2/observations", json={"observations": []}).status_code == 404
    assert (tmp_path / "data" / "program1.db").exists()


def test_worker_registry_is_available_through_program1_runtime(tmp_path: Path) -> None:
    write_runtime_config(tmp_path, "program1", "program1.db")

    app = create_runtime_app({"program1"}, default_profile="program1", project_root=tmp_path)
    client = TestClient(app)

    registered = client.post(
        "/api/v1/workers/register",
        json={
            "worker_id": "worker-runtime-01",
            "worker_type": "DISCOVERY_BROWSER_WORKER",
            "installation_id": "install-runtime-1",
            "version": "0.1.9",
            "capabilities": ["collector:shopee-current-page-lab-v2"],
        },
    )
    assert registered.status_code == 200
    assert registered.json()["health_state"] == "ONLINE_IDLE"

    beaten = client.post(
        "/api/v1/workers/worker-runtime-01/heartbeat",
        json={"health_state": "ONLINE_BUSY"},
    )
    assert beaten.status_code == 200
    assert beaten.json()["version_no"] == 2

    listed = client.get("/api/v1/workers")
    assert listed.status_code == 200
    assert [entry["worker_id"] for entry in listed.json()] == ["worker-runtime-01"]
    assert listed.json()[0]["health_state"] == "ONLINE_BUSY"
