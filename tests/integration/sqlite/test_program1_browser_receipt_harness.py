"""Exercise the browser lab's real HTTP/SQLite path without launching a browser."""

import importlib.util
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.integration


def test_browser_lab_receipts_are_saved_and_replayed_after_service_restart():
    path = Path(__file__).resolve().parents[3] / "tools/program1_chromium_restart_e2e.py"
    spec = importlib.util.spec_from_file_location("program1_browser_lab", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    backend = module.DeterministicProgram1Backend()
    backend.start()
    observation = {
        "observation_id": "http-observation",
        "platform": "shopee",
        "shop_id": "shop",
        "item_id": "item",
        "product_name": "Fixture",
        "collected_at": "2026-09-09T00:00:00Z",
        "source_job_id": "job",
    }
    try:
        with httpx.Client(base_url=backend.base_url, timeout=5) as client:
            first = client.post(
                "/api/v1/program1/observations",
                json={"batch_id": "first", "observations": [observation]},
            )
            assert first.status_code == 200
            assert first.json()["accepted_count"] == 1
            backend.restart_ingestion()
            payload = {"batch_id": "duplicate", "observations": [observation]}
            duplicate = client.post("/api/v1/program1/observations", json=payload)
            assert duplicate.json()["duplicate_count"] == 1
            backend.restart_ingestion()
            replay = client.post("/api/v1/program1/observations", json=payload)
            assert replay.json() == duplicate.json()
            assert backend.saved_counts() == {"observations": 1, "receipts": 2}
    finally:
        backend.stop()
