from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
import urllib.parse
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / ".browser-profiles" / "fixture-autorun"
EXTENSION_DIR = ROOT / "browser_plugin" / "program1"
BRAVE_EXE = Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")
EXTENSION_SCHEME = "chrome-extension://"
KNOWN_EXTENSION_ID = "mmljiahkjdnnphianfhgmdjjionggnji"  # stable for this unpacked path
TOTAL_PAGES = 2
PRODUCTS_PER_PAGE = 3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class FixtureBackend:
    """Serves a two-page deterministic Shopee-like fixture listing on /listing, plus
    a minimal Back Office mock (register/heartbeat/observations ACK) on /api/v1/..."""

    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []
        self.port = 0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler_factory())
        self.port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()

    def _handler_factory(self):
        backend = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args) -> None:  # quiet
                pass

            def _json(self, payload: dict[str, object], status: int = 200) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _html(self, body: str) -> None:
                content = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def do_GET(self) -> None:
                parsed = urllib.parse.urlsplit(self.path)
                if parsed.path == "/listing":
                    page = int(urllib.parse.parse_qs(parsed.query).get("page", ["0"])[0])
                    backend.requests.append({"method": "GET", "path": self.path, "page": page})
                    self._html(backend.listing_page(page))
                    return
                self.send_error(404)

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    payload = json.loads(raw.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    payload = {}
                backend.requests.append({"method": "POST", "path": self.path, "payload": payload})
                if self.path == "/api/v1/workers/register":
                    self._json(
                        {
                            "worker_id": payload.get("worker_id"),
                            "worker_type": payload.get("worker_type"),
                            "health_state": "ONLINE_IDLE",
                            "last_seen_at": datetime.now(UTC).isoformat(),
                            "version_no": 1,
                        }
                    )
                    return
                if self.path.endswith("/heartbeat"):
                    self._json(
                        {
                            "worker_id": self.path.split("/")[-2],
                            "last_seen_at": datetime.now(UTC).isoformat(),
                        }
                    )
                    return
                if self.path == "/api/v1/program1/observations":
                    # ACK shape mirrors the real Back Office endpoint (app.py):
                    # the extension's validateObservationBatchAck requires
                    # batch_id + received_count + accepted_count to match.
                    observations = payload.get("observations", [])
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

    def listing_page(self, page: int) -> str:
        page = max(0, min(page, TOTAL_PAGES - 1))
        is_last = page == TOTAL_PAGES - 1
        products = []
        for index in range(PRODUCTS_PER_PAGE):
            shop_id = f"9{page}01"
            item_id = f"{1000 + page * 100 + index}"
            name = f"Fixture SSD page {page + 1} item {index + 1}"
            products.append(
                f'<div data-program1-fixture-product data-platform="shopee" data-shop-id="{shop_id}" '
                f'data-item-id="{item_id}" data-name="{name}" '
                f'data-url="http://127.0.0.1:{self.port}/item-{page}-{index}">{name}</div>'
            )
        if is_last:
            controller = f"""
              <a class="shopee-button-no-outline" href="/listing?page=0">1</a>
              <a class="shopee-button-solid shopee-button-solid--primary" href="/listing?page={page}" aria-current="true">{page + 1}</a>
              <a class="shopee-icon-button shopee-icon-button--right shopee-icon-button--disabled" aria-disabled="true" href="/"><span>next</span></a>"""
        else:
            controller = f"""
              <a class="shopee-button-solid shopee-button-solid--primary" href="/listing?page={page}" aria-current="true">{page + 1}</a>
              <a class="shopee-button-no-outline" href="/listing?page={page + 1}">{page + 2}</a>
              <a class="shopee-icon-button shopee-icon-button--right" href="/listing?page={page + 1}"><span>next</span></a>"""
        return f"""<!doctype html><html><head><meta charset="utf-8"><title>Fixture listing page {page + 1}</title></head>
<body>
<section class="shopee-search-item-result">
  <div class="shopee-mini-page-controller">
    <span class="shopee-mini-page-controller__current">{page + 1}</span>/
    <span class="shopee-mini-page-controller__total">{TOTAL_PAGES}</span>
  </div>
  <nav aria-label="" class="shopee-page-controller">{controller}</nav>
  {''.join(products)}
</section>
</body></html>"""


async def extension_id_from_context(context) -> str | None:
    service_worker = next(iter(context.service_workers), None)
    if service_worker is None:
        try:
            service_worker = await asyncio.wait_for(context.wait_for_event("serviceworker"), 5)
        except TimeoutError:
            return None
    if not service_worker.url.startswith(EXTENSION_SCHEME):
        return None
    return service_worker.url.removeprefix(EXTENSION_SCHEME).split("/", maxsplit=1)[0]


async def read_panel(page) -> dict[str, str]:
    fields = {
        "state": "#state",
        "step": "#step",
        "last_error": "#lastError",
        "registry": "#registryStatus",
        "cycle": "#cycleCount",
        "captured": "#capturedCount",
        "accepted": "#acceptedCount",
        "delivered_batches": "#sentCount",
        "outbox": "#outboxCount",
        "session_accepted": "#sessionAcceptedCount",
        "rate": "#ratePerHour",
    }
    result = {}
    for key, selector in fields.items():
        if await page.locator(selector).count() == 0:
            result[key] = ""  # e.g. #lastError renders only when an error exists
            continue
        result[key] = (await page.text_content(selector)) or ""
    return result


async def set_range_value(page, selector: str, value: int) -> None:
    await page.evaluate(
        """([selector, value]) => {
            const el = document.querySelector(selector);
            el.value = String(value);
            el.dispatchEvent(new Event("input", { bubbles: true }));
        }""",
        [selector, value],
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end check of the pagination-aware auto-run against a deterministic "
        "two-page fixture listing + mock Back Office served locally on 127.0.0.1. Expects the run "
        "to walk page 1 -> 2 via the real next link and finish cleanly on the last page."
    )
    parser.add_argument("--profile-dir", default=str(PROFILE_DIR))
    parser.add_argument("--wipe", action="store_true", help="delete the profile before the run (re-grant the 127.0.0.1 permission once)")
    parser.add_argument("--worker-id", default="fixture-autorun")
    parser.add_argument("--delay-min", type=int, default=2)
    parser.add_argument("--delay-max", type=int, default=3)
    parser.add_argument("--prompt-wait", type=float, default=75.0)
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir).resolve()
    capture_dir = ROOT / ".browser-profiles" / "captures" / datetime.now(UTC).strftime("%Y-%m-%d") / "fixture-autorun"
    capture_dir.mkdir(parents=True, exist_ok=True)

    backend = FixtureBackend()
    backend.start()
    mock_url = f"http://127.0.0.1:{backend.port}"
    report: dict[str, object] = {
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mode": "fixture-listing-end-to-end",
        "extension_version": json.loads((EXTENSION_DIR / "manifest.json").read_text(encoding="utf-8"))["version"],
        "backend_mock_url": mock_url,
        "expect": f"finish on page {TOTAL_PAGES} of {TOTAL_PAGES} after {TOTAL_PAGES} cycles",
    }

    if args.wipe and profile_dir.exists():
        import shutil

        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                executable_path=str(BRAVE_EXE),
                headless=False,
                args=[
                    f"--disable-extensions-except={EXTENSION_DIR}",
                    f"--load-extension={EXTENSION_DIR}",
                ],
            )
            extension_id = await extension_id_from_context(context) or KNOWN_EXTENSION_ID
            panel_url = f"{EXTENSION_SCHEME}{extension_id}/dist/sidepanel.html"
            panel = await context.new_page()
            page_errors: list[str] = []

            async def capture_error(message) -> None:
                if message.type in ("error",) or (message.type == "warning" and "favicon" not in str(message.text)):
                    page_errors.append(f"panel:{message.type}: {message.text}")

            async def capture_pageerror(error) -> None:
                page_errors.append(f"pageerror: {error}")

            panel.on("console", capture_error)
            panel.on("pageerror", capture_pageerror)
            target_url = f"{mock_url}/listing?page=0"

            await panel.goto(f"{panel_url}#/settings", wait_until="domcontentloaded")
            await asyncio.sleep(0.6)
            await panel.fill("#backendUrl", mock_url)
            await panel.fill("#workerId", args.worker_id)
            await set_range_value(panel, "#delayMinSeconds", args.delay_min)
            await set_range_value(panel, "#delayMaxSeconds", args.delay_max)
            await panel.fill("#targetUrl", target_url)
            print(f"[setup] backend mock {mock_url} / worker {args.worker_id} / delay {args.delay_min}-{args.delay_max}s", flush=True)
            print("  -> if Brave asks to allow access to the local fixture host, click Allow now.", flush=True)
            await panel.click("#save")
            deadline = time.monotonic() + args.prompt_wait
            registry_text = ""
            while time.monotonic() < deadline:
                registry_text = (await panel.text_content("#registryStatus")) or ""
                if "registered (" in registry_text:
                    break
                await asyncio.sleep(1)
            print(f"[setup] {registry_text}", flush=True)
            if "registered (" not in registry_text:
                report["aborted"] = "registry not confirmed; permission prompt needs an Allow click"
                print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
                await context.close()
                return

            await panel.goto(f"{panel_url}#/status", wait_until="domcontentloaded")
            await asyncio.sleep(0.6)
            await panel.click("#startAuto")

            transcript: list[dict[str, str]] = []
            previous = ""
            deadline = time.monotonic() + 120
            final_step = ""
            while time.monotonic() < deadline:
                view = await read_panel(panel)
                key = f"{view['state']} | {view['step']}"
                if key != previous:
                    transcript.append({"at": datetime.now(UTC).isoformat(timespec="seconds"), "state": view["state"], "step": view["step"]})
                    print(f"[run] {view['state']} | {view['step']}", flush=True)
                    previous = key
                running = (await panel.get_attribute("#startAuto", "disabled")) is not None
                terminal = view["step"].startswith("Auto run finished") or view["step"].startswith("Auto run stopped")
                if not running and terminal:
                    await asyncio.sleep(1.0)
                    view = await read_panel(panel)
                    final_step = view["step"]
                    print(f"[run] FINAL | {view['step']}", flush=True)
                    break
                await asyncio.sleep(0.15)

            report["final_step"] = final_step
            report["metrics"] = await read_panel(panel)
            report["last_payload"] = (await panel.text_content("#status")) or ""
            if await panel.locator("#lastError").count():
                report["last_error_line"] = (await panel.text_content("#lastError")) or ""
            report["transcript"] = transcript
            report["page_errors"] = page_errors
            report["finished_cleanly"] = final_step.startswith(
                f"Auto run finished: reached the last page (page {TOTAL_PAGES} of {TOTAL_PAGES})"
            )

            await panel.screenshot(path=str(capture_dir / "panel_final.png"))
            for page in context.pages:
                if page.url.startswith(mock_url) and "/listing" in page.url:
                    await page.screenshot(path=str(capture_dir / "fixture_last_page.png"))
                    report["last_fixture_url"] = page.url
                    break
            await context.close()

        # Mock server request log = the durable assertion source. Each fixture
        # observation carries product_url `/item-<page>-<index>`.
        import re

        batches = [entry for entry in backend.requests if entry.get("path") == "/api/v1/program1/observations"]
        accepted_total = sum(len((entry.get("payload") or {}).get("observations", [])) for entry in batches)
        pages_seen: set[int] = set()
        for entry in batches:
            for observation in (entry.get("payload") or {}).get("observations", []):
                match = re.search(r"/item-(\d)-", str(observation.get("product_url", "")))
                if match:
                    pages_seen.add(int(match.group(1)))
        report["backend_log"] = {
            "register_calls": sum(1 for e in backend.requests if e.get("path") == "/api/v1/workers/register"),
            "heartbeat_calls": sum(1 for e in backend.requests if "heartbeat" in str(e.get("path"))),
            "observation_batches": len(batches),
            "accepted_observations_total": accepted_total,
            "delivered_page_numbers": sorted(pages_seen),
        }
    finally:
        backend.stop()

    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    report_path = capture_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[report] {report_path}", flush=True)

    if not bool(report.get("finished_cleanly")):
        raise SystemExit("FAIL: auto-run did not finish cleanly on the last fixture page")


if __name__ == "__main__":
    asyncio.run(main())
