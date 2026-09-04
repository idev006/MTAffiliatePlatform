from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import tempfile
import threading
import time
import urllib.parse
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, async_playwright

ROOT = Path(__file__).resolve().parents[1]
EXTENSION_DIR = ROOT / "browser_plugin" / "program1"
EXTENSION_SCHEME = "chrome-extension://"
WORKER_ID = "ci-program1-browser-worker"
JOB_ID = "ci-program1-discovery-job"
LEASE_TOKEN = "ci-lease-token"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class DeterministicProgram1Backend:
    def __init__(self) -> None:
        self.port = 0
        self.job_state = "QUEUED"
        self.lease_token = LEASE_TOKEN
        self.lease_until = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
        self.lease_count = 0
        self.register_count = 0
        self.renew_count = 0
        self.checkpoints: list[dict[str, Any]] = []
        self.observation_batches: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler_factory())
        self.port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "job_state": self.job_state,
                "lease_count": self.lease_count,
                "register_count": self.register_count,
                "renew_count": self.renew_count,
                "checkpoints": list(self.checkpoints),
                "observation_batches": list(self.observation_batches),
                "requests": list(self.requests),
            }

    def fixture_page(self, page: int) -> str:
        page = 0 if page <= 0 else 1
        name = f"Fixture SSD page {page + 1}"
        item_id = str(2000 + page)
        if page == 0:
            nav = """
            <a class="shopee-button-solid shopee-button-solid--primary"
               href="/listing?page=0" aria-current="true">1</a>
            <a class="shopee-button-no-outline" href="/listing?page=1">2</a>
            <a class="shopee-icon-button shopee-icon-button--right"
               href="/listing?page=1">next</a>
            """
        else:
            nav = """
            <a class="shopee-button-no-outline" href="/listing?page=0">1</a>
            <a class="shopee-button-solid shopee-button-solid--primary"
               href="/listing?page=1" aria-current="true">2</a>
            <a class="shopee-icon-button shopee-icon-button--right shopee-icon-button--disabled"
               aria-disabled="true" href="/">next</a>
            """
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{name}</title></head>
<body>
<section class="shopee-search-item-result">
  <span class="shopee-mini-page-controller__total">2</span>
  <nav class="shopee-page-controller" role="navigation">{nav}</nav>
  <div data-program1-fixture-product
       data-platform="shopee"
       data-shop-id="9001"
       data-item-id="{item_id}"
       data-name="{name}"
       data-url="{self.base_url}/item/{item_id}">{name}</div>
</section>
</body></html>"""

    def _job_payload(self) -> dict[str, Any]:
        return {
            "job_id": JOB_ID,
            "job_type": "DISCOVER_PRODUCTS",
            "payload_ref": "plan:ci-browser-e2e",
            "lease_token": self.lease_token if self.job_state != "COMPLETED" else None,
            "lease_until": self.lease_until if self.job_state != "COMPLETED" else None,
            "state": self.job_state,
        }

    def _handler_factory(self):
        backend = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args: object) -> None:
                return

            def _record(self, method: str, payload: Any = None) -> None:
                with backend._lock:
                    backend.requests.append({"method": method, "path": self.path, "payload": payload})

            def _json(self, payload: Any, status: int = 200) -> None:
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _html(self, body: str) -> None:
                raw = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _body(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                return json.loads(raw.decode("utf-8") or "{}")

            def do_GET(self) -> None:
                parsed = urllib.parse.urlsplit(self.path)
                self._record("GET")
                if parsed.path == "/listing":
                    page = int(urllib.parse.parse_qs(parsed.query).get("page", ["0"])[0])
                    self._html(backend.fixture_page(page))
                    return
                if parsed.path == f"/api/v1/program1/discovery-jobs/{JOB_ID}/work-package":
                    self._json(
                        {
                            "hypothesis": {"hypothesis_id": "hyp-ci-browser-e2e"},
                            "signals": [{"signal_id": "identity"}],
                            "discovery_plan": {
                                "plan_id": "plan-ci-browser-e2e",
                                "collection_targets": [f"{backend.base_url}/listing?page=0"],
                                "capability_requirements": ["collector:fixture-profile-v1"],
                            },
                        }
                    )
                    return
                if parsed.path == f"/api/v1/jobs/{JOB_ID}":
                    with backend._lock:
                        payload = backend._job_payload()
                    self._json(payload)
                    return
                self.send_error(404)

            def do_POST(self) -> None:
                payload = self._body()
                self._record("POST", payload)

                if self.path == "/api/v1/workers/register":
                    with backend._lock:
                        backend.register_count += 1
                    self._json(
                        {
                            "worker_id": payload.get("worker_id"),
                            "worker_type": payload.get("worker_type"),
                            "health_state": "ONLINE_IDLE",
                            "last_seen_at": utc_now(),
                            "version_no": backend.register_count,
                        }
                    )
                    return

                if self.path.endswith("/heartbeat"):
                    self._json(
                        {
                            "worker_id": self.path.split("/")[-2],
                            "health_state": payload.get("health_state"),
                            "last_seen_at": utc_now(),
                            "version_no": 1,
                        }
                    )
                    return

                if self.path == "/api/v1/jobs/lease-next":
                    with backend._lock:
                        if backend.lease_count == 0 and backend.job_state == "QUEUED":
                            backend.lease_count += 1
                            backend.job_state = "LEASED"
                            response = backend._job_payload()
                        else:
                            response = None
                    self._json(response)
                    return

                if self.path == f"/api/v1/jobs/{JOB_ID}/start":
                    with backend._lock:
                        backend.job_state = "IN_PROGRESS"
                        response = backend._job_payload()
                    self._json(response)
                    return

                if self.path == f"/api/v1/jobs/{JOB_ID}/renew":
                    with backend._lock:
                        backend.renew_count += 1
                        backend.lease_until = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
                        response = backend._job_payload()
                    self._json(response)
                    return

                if self.path == f"/api/v1/jobs/{JOB_ID}/checkpoint":
                    with backend._lock:
                        backend.checkpoints.append(payload)
                        response = backend._job_payload()
                    self._json(response)
                    return

                if self.path == f"/api/v1/jobs/{JOB_ID}/verify":
                    with backend._lock:
                        backend.job_state = "VERIFYING"
                        response = backend._job_payload()
                    self._json(response)
                    return

                if self.path == f"/api/v1/jobs/{JOB_ID}/complete":
                    with backend._lock:
                        backend.job_state = "COMPLETED"
                        response = backend._job_payload()
                    self._json(response)
                    return

                if self.path == "/api/v1/program1/observations":
                    observations = payload.get("observations") or []
                    with backend._lock:
                        backend.observation_batches.append(payload)
                    self._json(
                        {
                            "batch_id": payload.get("batch_id"),
                            "received_count": len(observations),
                            "accepted_count": len(observations),
                        }
                    )
                    return

                self.send_error(404)

        return Handler


async def extension_id_from_context(context: BrowserContext) -> str:
    worker = next(iter(context.service_workers), None)
    if worker is None:
        worker = await asyncio.wait_for(context.wait_for_event("serviceworker"), timeout=10)
    if not worker.url.startswith(EXTENSION_SCHEME):
        raise RuntimeError(f"unexpected service worker URL: {worker.url}")
    return worker.url.removeprefix(EXTENSION_SCHEME).split("/", 1)[0]


async def extension_command(page, message: dict[str, Any]) -> dict[str, Any]:
    result = await page.evaluate(
        """async (message) => {
          return await chrome.runtime.sendMessage(message);
        }""",
        message,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"extension returned non-object response: {result!r}")
    return result


async def open_control_page(context: BrowserContext, extension_id: str):
    page = await context.new_page()
    await page.goto(f"{EXTENSION_SCHEME}{extension_id}/dist/sidepanel.html", wait_until="domcontentloaded")
    return page


async def configure_worker(page, backend_url: str) -> None:
    await page.evaluate(
        """async ([backendUrl, workerId]) => {
          await chrome.storage.local.set({
            program1_worker_settings_v1: {
              backend_url: backendUrl,
              worker_id: workerId,
              target_url: "",
              page_load_wait_seconds: 1,
              page_retry_wait_seconds: 1,
              max_page_retries: 1,
              delay_min_seconds: 30,
              delay_max_seconds: 30
            }
          });
        }""",
        [backend_url, WORKER_ID],
    )


async def wait_until(predicate, *, timeout: float, interval: float = 0.1, label: str) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(interval)
    raise TimeoutError(f"timed out waiting for {label}")


async def launch_context(playwright, profile_dir: Path) -> BrowserContext:
    return await playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
        args=[
            f"--disable-extensions-except={EXTENSION_DIR}",
            f"--load-extension={EXTENSION_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )


async def run_scenario(profile_dir: Path) -> dict[str, Any]:
    if not (EXTENSION_DIR / "dist" / "sidepanel.html").exists():
        raise RuntimeError("extension dist/ is missing; run npm run build first")

    backend = DeterministicProgram1Backend()
    backend.start()
    report: dict[str, Any] = {
        "started_at": utc_now(),
        "extension_version": json.loads((EXTENSION_DIR / "manifest.json").read_text())["version"],
        "backend_url": backend.base_url,
        "profile_dir": str(profile_dir),
    }

    try:
        async with async_playwright() as playwright:
            context1 = await launch_context(playwright, profile_dir)
            extension_id = await extension_id_from_context(context1)
            control1 = await open_control_page(context1, extension_id)
            await configure_worker(control1, backend.base_url)

            registration = await extension_command(control1, {"type": "PROGRAM1_REGISTER_WORKER"})
            if not registration.get("ok"):
                raise RuntimeError(f"registration failed: {registration}")

            started = await extension_command(control1, {"type": "PROGRAM1_START_BACKGROUND_RUN"})
            if not started.get("ok"):
                raise RuntimeError(f"background start failed: {started}")

            await wait_until(
                lambda: len(backend.snapshot()["checkpoints"]) >= 1,
                timeout=20,
                label="first durable page checkpoint",
            )

            status_before = await extension_command(control1, {"type": "PROGRAM1_GET_PROCESS_STATUS"})
            if status_before.get("active_job", {}).get("job_id") != JOB_ID:
                raise AssertionError(f"active job missing before restart: {status_before}")
            if not status_before.get("run_state", {}).get("desired"):
                raise AssertionError(f"run state not durable before restart: {status_before}")
            if "page=1" not in str(status_before.get("run_state", {}).get("current_target_url")):
                raise AssertionError(f"next target not checkpointed before restart: {status_before}")

            report["before_restart"] = status_before
            report["backend_before_restart"] = backend.snapshot()
            await context1.close()

            context2 = await launch_context(playwright, profile_dir)
            extension_id2 = await extension_id_from_context(context2)
            if extension_id2 != extension_id:
                raise AssertionError(f"extension id changed across restart: {extension_id} -> {extension_id2}")
            control2 = await open_control_page(context2, extension_id2)

            await wait_until(
                lambda: backend.snapshot()["renew_count"] >= 1,
                timeout=15,
                label="startup reconcile/renew",
            )
            status_after = await extension_command(control2, {"type": "PROGRAM1_GET_PROCESS_STATUS"})
            if status_after.get("active_job", {}).get("job_id") != JOB_ID:
                raise AssertionError(f"active job not recovered after restart: {status_after}")
            if not status_after.get("run_state", {}).get("desired"):
                raise AssertionError(f"desired run state lost after restart: {status_after}")

            await wait_until(
                lambda: backend.snapshot()["job_state"] == "COMPLETED",
                timeout=25,
                label="job completion after restart",
            )
            await asyncio.sleep(0.5)
            final_status = await extension_command(control2, {"type": "PROGRAM1_GET_PROCESS_STATUS"})
            snapshot = backend.snapshot()

            if len(snapshot["observation_batches"]) != 2:
                raise AssertionError(f"expected exactly 2 observation batches, got {len(snapshot['observation_batches'])}")
            observed_items = [
                observation["item_id"]
                for batch in snapshot["observation_batches"]
                for observation in batch.get("observations", [])
            ]
            if observed_items != ["2000", "2001"]:
                raise AssertionError(f"unexpected/duplicate observation lineage: {observed_items}")
            if len(snapshot["checkpoints"]) != 2:
                raise AssertionError(f"expected exactly 2 checkpoints, got {len(snapshot['checkpoints'])}")
            if snapshot["lease_count"] != 1:
                raise AssertionError(f"job was leased more than once: {snapshot['lease_count']}")
            if final_status.get("active_job") is not None:
                raise AssertionError(f"local active job not cleared: {final_status}")
            if final_status.get("run_state", {}).get("desired"):
                raise AssertionError(f"run still desired after completion: {final_status}")
            if not final_status.get("run_state", {}).get("terminal"):
                raise AssertionError(f"terminal flag missing after completion: {final_status}")
            if final_status.get("outbox_remaining_count") != 0:
                raise AssertionError(f"outbox not empty after completion: {final_status}")

            report["after_restart"] = status_after
            report["final_status"] = final_status
            report["backend_final"] = snapshot
            report["passed"] = True
            await context2.close()
    finally:
        backend.stop()

    return report


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic real-Chromium Program 1 MV3 restart/reconcile E2E. No Shopee or operator UI interaction."
    )
    parser.add_argument("--profile-dir", default=None)
    parser.add_argument("--keep-profile", action="store_true")
    args = parser.parse_args()

    owned_temp = args.profile_dir is None
    profile_dir = Path(args.profile_dir).resolve() if args.profile_dir else Path(tempfile.mkdtemp(prefix="mta-p1-e2e-"))
    if profile_dir.exists() and owned_temp:
        # tempfile already creates it; Chromium requires an empty usable directory.
        pass
    else:
        profile_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = await run_scenario(profile_dir)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    finally:
        if owned_temp and not args.keep_profile:
            shutil.rmtree(profile_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
