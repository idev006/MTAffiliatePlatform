from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from websocket import WebSocket, WebSocketException

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "program1.db"
DEFAULT_LOG = ROOT / "logs" / "program1-monitor.ndjson"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class Target:
    title: str
    url: str
    websocket_url: str


def read_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def cdp_targets(port: int) -> list[dict[str, Any]]:
    try:
        data = read_json(f"http://127.0.0.1:{port}/json/list")
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def find_target(port: int, predicate) -> Target | None:
    for item in cdp_targets(port):
        if not isinstance(item, dict) or item.get("type") != "page":
            continue
        url = str(item.get("url") or "")
        title = str(item.get("title") or "")
        websocket_url = str(item.get("webSocketDebuggerUrl") or "")
        if websocket_url and predicate(url, title):
            return Target(title=title, url=url, websocket_url=websocket_url)
    return None


def cdp_evaluate(websocket_url: str, expression: str) -> Any:
    socket = WebSocket()
    try:
        socket.connect(websocket_url, timeout=5)
    except WebSocketException as error:
        return {"ok": False, "error": f"CDP_WEBSOCKET_UNAVAILABLE: {error}"}
    try:
        request = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        }
        socket.send(json.dumps(request))
        while True:
            try:
                message = json.loads(socket.recv())
            except (OSError, WebSocketException, json.JSONDecodeError) as error:
                return {"ok": False, "error": f"CDP_RECEIVE_FAILED: {error}"}
            if message.get("id") == 1:
                if "exceptionDetails" in message:
                    return {"ok": False, "error": "CDP_EVALUATE_EXCEPTION"}
                return message.get("result", {}).get("result", {}).get("value")
    finally:
        socket.close()


def shopee_status(port: int) -> dict[str, Any]:
    target = find_target(port, lambda url, _title: url.startswith("https://shopee.co.th/"))
    if target is None:
        return {"ok": False, "error": "SHOPEE_TAB_NOT_FOUND"}
    value = cdp_evaluate(
        target.websocket_url,
        """(() => {
          const identityAnchors = [...document.querySelectorAll('a[href]')]
            .filter((anchor) => /(?:^|-)i\\.\\d+\\.\\d+(?:\\?|\\/|$)/.test(anchor.getAttribute('href') || ''));
          const nextButton = document.querySelector('.shopee-icon-button--right, button[aria-label*="next" i]');
          return {
            url: location.href,
            title: document.title,
            captcha_or_blocked: location.href.includes('/verify/') || Boolean(document.querySelector('iframe[src*="captcha"], input[name*="captcha" i]')),
            search_item_count: document.querySelectorAll('li.shopee-search-item-result__item[data-sqe="item"]').length,
            identity_anchor_count: identityAnchors.length,
            next_enabled: Boolean(nextButton && !nextButton.disabled && !nextButton.className.includes('disabled')),
          };
        })()""",
    )
    return {"ok": True, **(value if isinstance(value, dict) else {"value": value})}


def worker_status(port: int) -> dict[str, Any]:
    target = find_target(
        port,
        lambda url, _title: url.endswith("/src/sidepanel.html")
        or "/dist/sidepanel.html" in url,
    )
    if target is None:
        return {"ok": False, "error": "WORKER_UI_NOT_FOUND"}
    value = cdp_evaluate(
        target.websocket_url,
        """(() => new Promise((resolve) => {
          const send = (message) => new Promise((done) => {
            chrome.runtime.sendMessage(message, (response) => {
              done(response || { ok: false, error: chrome.runtime.lastError?.message || 'NO_RESPONSE' });
            });
          });
          Promise.all([
            send({ type: 'PROGRAM1_GET_SETTINGS' }),
            send({ type: 'PROGRAM1_GET_RUN_STATE' }),
          ]).then(([settingsResponse, runResponse]) => {
            const settings = settingsResponse?.settings || {};
            resolve({
              state: document.querySelector('#state')?.textContent || null,
              step: document.querySelector('#step')?.textContent || null,
              error: document.querySelector('#lastError')?.textContent || null,
              captured: Number(document.querySelector('#capturedCount')?.textContent || 0),
              accepted: Number(document.querySelector('#acceptedCount')?.textContent || 0),
              queued: Number(document.querySelector('#queuedCount')?.textContent || 0),
              delivered_batches: Number(document.querySelector('#sentCount')?.textContent || 0),
              outbox: Number(document.querySelector('#outboxCount')?.textContent || 0),
              backend_url: settings.backend_url || document.querySelector('#backendUrl')?.value || null,
              worker_id: settings.worker_id || document.querySelector('#workerId')?.value || null,
              target_url: settings.target_url || document.querySelector('#targetUrl')?.value || null,
              delay_range: settings.delay_min_seconds !== undefined && settings.delay_max_seconds !== undefined
                ? `${settings.delay_min_seconds}-${settings.delay_max_seconds}`
                : document.querySelector('#delayRangeLabel')?.textContent || null,
              page_load_wait_seconds: settings.page_load_wait_seconds ?? null,
              page_retry_wait_seconds: settings.page_retry_wait_seconds ?? null,
              max_page_retries: settings.max_page_retries ?? null,
              auto_resume: settings.auto_resume ?? null,
              advance_after_delivery: settings.advance_after_delivery ?? null,
              run_state: runResponse?.run_state || null,
              start_disabled: Boolean(document.querySelector('#startAuto')?.disabled),
              stop_disabled: Boolean(document.querySelector('#stopAuto')?.disabled),
            });
          });
        }))()""",
    )
    return {"ok": True, **(value if isinstance(value, dict) else {"value": value})}


def database_status(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"ok": False, "error": "DATABASE_NOT_FOUND", "path": str(db_path)}
    with sqlite3.connect(db_path) as connection:
        product_count = connection.execute("select count(*) from product_observations").fetchone()[0]
        batch_count = connection.execute("select count(*) from ingestion_batches").fetchone()[0]
        latest = connection.execute(
            """
            select observation_id, product_name, source_worker_id, source_query, extractor_version
            from product_observations
            order by id desc
            limit 1
            """
        ).fetchone()
    return {
        "ok": True,
        "product_observation_count": product_count,
        "ingestion_batch_count": batch_count,
        "latest_observation": list(latest) if latest else None,
    }


def monitor_status(port: int, db_path: Path) -> dict[str, Any]:
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "shopee": shopee_status(port),
        "worker": worker_status(port),
        "database": database_status(db_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor Program 1 Brave direct worker activity.")
    parser.add_argument("--debugging-port", type=int, default=9223)
    parser.add_argument("--db-path", default=str(DEFAULT_DB))
    parser.add_argument("--interval-seconds", type=float, default=30)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--log-path", default=str(DEFAULT_LOG))
    args = parser.parse_args()

    log_path = Path(args.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    db_path = Path(args.db_path)

    previous_url = None
    previous_count = None
    first_count = None
    first_seen_at = None
    stagnant_samples = 0

    for index in range(args.samples):
        status = monitor_status(args.debugging_port, db_path)
        now = time.monotonic()
        current_url = status["shopee"].get("url") if isinstance(status["shopee"], dict) else None
        current_count = (
            status["database"].get("product_observation_count")
            if isinstance(status["database"], dict)
            else None
        )
        if isinstance(current_count, int) and first_count is None:
            first_count = current_count
            first_seen_at = now
        if current_url == previous_url and current_count == previous_count:
            stagnant_samples += 1
        else:
            stagnant_samples = 0
        previous_url = current_url
        previous_count = current_count
        rate_per_hour = 0
        projected_8h = 0
        if isinstance(current_count, int) and isinstance(first_count, int) and first_seen_at is not None:
            elapsed_hours = max((now - first_seen_at) / 3600, 1 / 3600)
            produced = max(current_count - first_count, 0)
            rate_per_hour = round(produced / elapsed_hours)
            projected_8h = rate_per_hour * 8
        status["monitor"] = {
            "sample": index + 1,
            "stagnant_samples": stagnant_samples,
            "stuck_suspected": stagnant_samples >= 3,
            "rate_per_hour": rate_per_hour,
            "projected_8h_observations": projected_8h,
        }
        line = json.dumps(status, ensure_ascii=False)
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if index < args.samples - 1:
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
