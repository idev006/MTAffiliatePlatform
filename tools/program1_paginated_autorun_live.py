from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / ".browser-profiles" / "autorun-guest"
EXTENSION_DIR = ROOT / "browser_plugin" / "program1"
BRAVE_EXE = Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")
EXTENSION_SCHEME = "chrome-extension://"
KNOWN_EXTENSION_ID = "mmljiahkjdnnphianfhgmdjjionggnji"  # stable for this unpacked path
SEARCH_TEMPLATE = "https://shopee.co.th/search?keyword={keyword}"
# Probe keywords in order; the driver picks the first listing with 2..5 pages so the
# auto-run exercises the real next-link advance at least once and then finishes on the
# genuine last page. Single-page listings still validate the clean finish path.
KEYWORDS = ["SATA SSD 512GB", "Fikwot FS810", "Ediloca ES106", "HIKSEMI E100"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


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


async def wait_for_selector_text(page, selector: str, contains: str, timeout_s: float) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        text = (await page.text_content(selector)) or ""
        if contains in text:
            return text
        await asyncio.sleep(1)
    return (await page.text_content(selector)) or ""


async def read_panel(page) -> dict[str, str]:
    fields = {
        "state": "#state",
        "step": "#step",
        "last_event": "#lastEvent",
        "registry": "#registryStatus",
        "last_error": "#lastError",
        "cycle": "#cycleCount",
        "captured": "#capturedCount",
        "accepted": "#acceptedCount",
        "delivered_batches": "#sentCount",
        "outbox": "#outboxCount",
    }
    result = {}
    for key, selector in fields.items():
        result[key] = (await page.text_content(selector)) or ""
    result["status_json"] = (await page.text_content("#status")) or ""
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


def shopee_pages(context) -> list:
    return [page for page in context.pages if page.url.startswith("https://shopee.co.th")]


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Live-run the 0.1.13 Program 1 auto-run against a real Shopee listing in a "
        "fresh guest profile (the flagged logged-in profile is never touched). Solves no "
        "CAPTCHA itself: the operator clicks any permission prompts / verification sliders."
    )
    parser.add_argument("--profile-dir", default=str(PROFILE_DIR))
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--worker-id", default="autorun-live-guest")
    parser.add_argument("--delay-min", type=int, default=5)
    parser.add_argument("--delay-max", type=int, default=8)
    parser.add_argument("--prompt-wait", type=float, default=75.0)
    parser.add_argument("--page-load-wait", type=float, default=6.0)
    parser.add_argument("--db", default=str(ROOT / "data" / "program1.db"))
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir).resolve()
    capture_dir = ROOT / ".browser-profiles" / "captures" / datetime.now(UTC).strftime("%Y-%m-%d") / "autorun-live"
    capture_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "started_at": now_iso(),
        "mode": "fresh-guest-context",
        "extension_version": (json.loads((EXTENSION_DIR / "manifest.json").read_text(encoding="utf-8")))["version"],
        "profile_dir": str(profile_dir),
        "probes": [],
        "run": None,
    }

    # Fresh profile every time: a stale service worker from an earlier extension version
    # is exactly the failure mode observed during registry E2E.
    if profile_dir.exists():
        import shutil

        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

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

        async def goto_route(route: str) -> None:
            await panel.goto(f"{panel_url}#/{route}", wait_until="domcontentloaded")
            await asyncio.sleep(0.5)  # Vue route render

        await goto_route("settings")
        await panel.fill("#backendUrl", args.backend_url)
        await panel.fill("#workerId", args.worker_id)
        await set_range_value(panel, "#delayMinSeconds", args.delay_min)
        await set_range_value(panel, "#delayMaxSeconds", args.delay_max)
        print(f"[panel] Save Settings -> {args.backend_url} / {args.worker_id} / delay {args.delay_min}-{args.delay_max}s", flush=True)
        print("  -> if Brave asks to allow access to the Back Office host, click Allow now.", flush=True)
        await panel.click("#save")
        await wait_for_selector_text(panel, "#registryStatus", "registered (", args.prompt_wait)
        report["registration"] = (await panel.text_content("#registryStatus")) or ""
        print(f"[panel] {report['registration']}", flush=True)
        if "registered (" not in str(report["registration"]):
            report["aborted"] = "registry not confirmed within prompt window"
            print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
            await context.close()
            return

        def search_url(keyword: str) -> str:
            return SEARCH_TEMPLATE.format(keyword=urllib.parse.quote(keyword))

        # ---- Probe phase: learn real page counts before choosing the run target. ----
        probes = report["probes"]
        chosen: dict[str, object] | None = None
        fallback_single: dict[str, object] | None = None
        for keyword in KEYWORDS:
            url = search_url(keyword)
            print(f"[probe] {keyword}: opening {url}", flush=True)
            await goto_route("settings")
            await panel.fill("#targetUrl", url)  # v-model keeps the panel store in sync
            await goto_route("status")
            await panel.click("#openTarget")
            await asyncio.sleep(args.page_load_wait)
            print("  -> if a Shopee verification slider/page appears, handle it now (this is the first Shopee touch from this guest profile).", flush=True)
            await panel.click("#capture")
            deadline = time.monotonic() + 40
            state = ""
            while time.monotonic() < deadline:
                state = (await panel.text_content("#state")) or ""
                if state not in ("LOADING", "COLLECTING", "READY", "IDLE", "QUEUED"):
                    break
                await asyncio.sleep(1)
            view = await read_panel(panel)
            probe: dict[str, object] = {"keyword": keyword, "url": url, "state": view["state"], "step": view["step"]}
            try:
                payload = json.loads(view["status_json"])
                probe["status_json"] = payload
                pagination = payload.get("pagination")
                if pagination is not None:
                    probe["total_pages"] = pagination.get("total_pages")
                    probe["has_next"] = pagination.get("has_next")
            except json.JSONDecodeError:
                pass
            probes.append(probe)
            print(f"[probe] {keyword}: state={probe['state']} step={probe['step']!r} total={probe.get('total_pages')}", flush=True)

            total = probe.get("total_pages")
            if isinstance(total, int):
                if 2 <= total <= 5 and chosen is None:
                    chosen = {"keyword": keyword, "total_pages": total}
                elif total == 1 and fallback_single is None:
                    fallback_single = {"keyword": keyword, "total_pages": total}

            if chosen is not None:
                break
            if probe.get("state") in ("PAGE_BLOCKED_BY_ANTIBOT",):
                break  # guest context is blocked too; do not keep hammering

        run_keyword = chosen if chosen is not None else fallback_single
        if run_keyword is None:
            report["aborted"] = "no usable listing and/or guest context blocked by Shopee verification"
            print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
            await context.close()
            return

        # ---- Run phase: target page 0 and let the auto-run walk to the real last page. ----
        keyword = str(run_keyword["keyword"])
        total_pages = int(run_keyword["total_pages"])
        url = search_url(keyword)
        print(f"[run] {keyword}: {total_pages} page(s); starting auto-run at page 1 -> expecting a real next-link advance and a clean finish on page {total_pages}.", flush=True)
        await goto_route("settings")
        await panel.fill("#targetUrl", url)
        await goto_route("status")
        await panel.click("#startAuto")

        transcript: list[dict[str, str]] = []
        previous = ""
        last_payload = ""
        deadline = time.monotonic() + 20 + total_pages * 45
        while time.monotonic() < deadline:
            view = await read_panel(panel)
            key = f"{view['state']} | {view['step']}"
            if key != previous:
                transcript.append({"at": now_iso(), "state": view["state"], "step": view["step"]})
                print(f"[run] {view['state']} | {view['step']}", flush=True)
                previous = key
                last_payload = view["status_json"]
            running = (await panel.get_attribute("#startAuto", "disabled")) is not None
            if not running and transcript:
                # Start button re-enabled => auto-run reached a terminal state.
                await asyncio.sleep(1.5)
                view = await read_panel(panel)
                key = f"{view['state']} | {view['step']}"
                if key != previous:
                    transcript.append({"at": now_iso(), "state": view["state"], "step": view["step"]})
                    print(f"[run] {view['state']} | {view['step']}", flush=True)
                    previous = key
                    last_payload = view["status_json"]
                break
            await asyncio.sleep(1)

        view = await read_panel(panel)
        metrics = {
            "cycle": view["cycle"],
            "captured": view["captured"],
            "accepted": view["accepted"],
            "delivered_batches": view["delivered_batches"],
            "outbox": view["outbox"],
        }
        report["run"] = {
            "keyword": keyword,
            "url": url,
            "transcript": transcript,
            "final_state": view["state"],
            "final_step": view["step"],
            "metrics": metrics,
            "final_status_json": last_payload,
        }
        report["finished_at"] = now_iso()

        # Screenshots: panel + the final Shopee page showing the last-page controller.
        await panel.screenshot(path=str(capture_dir / "panel_final.png"))
        report["screenshots"] = []
        for page in shopee_pages(context):
            if urllib.parse.quote(keyword) in page.url or keyword in urllib.parse.unquote(page.url):
                await page.screenshot(path=str(capture_dir / "shopee_last_page.png"))
                report["screenshots"].append(str(capture_dir / "shopee_last_page.png"))
                report["last_shopee_url"] = page.url
                break
        await context.close()

    # ---- Backend verification: rows actually landed in SQLite from the real browser. ----
    try:
        connection = sqlite3.connect(args.db)
        columns = [row[1] for row in connection.execute("PRAGMA table_info(product_observations)")]
        if "source_worker_id" in columns:
            row = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT observation_id) FROM product_observations "
                "WHERE source_worker_id = ?",
                (args.worker_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT observation_id) FROM product_observations "
                "WHERE extractor_version LIKE 'shopee-current-page-lab%'",
            ).fetchone()
        report["backend_sqlite"] = {
            "rows": row[0],
            "distinct_observation_ids": row[1],
            "matched_on": "source_worker_id" if "source_worker_id" in columns else "extractor_version",
        }
        connection.close()
    except sqlite3.Error as error:
        report["backend_sqlite"] = {"error": str(error)}

    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    report_path = capture_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[report] {report_path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
