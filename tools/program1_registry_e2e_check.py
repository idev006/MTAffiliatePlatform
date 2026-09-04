from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / ".browser-profiles" / "shopee-program1-visible"
EXTENSION_DIR = ROOT / "browser_plugin" / "program1"
BRAVE_EXE = Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")
EXTENSION_SCHEME = "chrome-extension://"
KNOWN_EXTENSION_ID = "mmljiahkjdnnphianfhgmdjjionggnji"  # stable for this unpacked path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def backend_worker(url: str, worker_id: str) -> dict[str, object] | None:
    try:
        with urllib.request.urlopen(f"{url}/api/v1/workers/{worker_id}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:  # noqa: BLE001 - network boundary, report shape matters
        return {"error": str(error)}


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


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open the Program 1 side panel in headed Brave and verify worker registration "
        "against a running Back Office API. Fill settings, click Save Settings, and click Allow if "
        "Brave asks for the local Back Office host permission."
    )
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--worker-id", default="worker-e2e-browser")
    parser.add_argument("--profile-dir", default=str(PROFILE_DIR))
    parser.add_argument("--wait-seconds", type=float, default=60.0)
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    if not BRAVE_EXE.exists():
        raise SystemExit(f"Brave executable not found: {BRAVE_EXE}")
    if not (EXTENSION_DIR / "manifest.json").exists():
        raise SystemExit(f"Extension manifest not found: {EXTENSION_DIR / 'manifest.json'}")

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
        page = await context.new_page()
        panel_url = f"{EXTENSION_SCHEME}{extension_id}/dist/sidepanel.html"
        await page.goto(panel_url, wait_until="domcontentloaded")

        # Settings live on the #/settings route; the registry line is in the header
        # and therefore visible on every route of the routed Vue panel.
        await page.goto(f"{panel_url}#/settings", wait_until="domcontentloaded")
        await page.fill("#backendUrl", args.backend_url)
        await page.fill("#workerId", args.worker_id)
        print(f"Clicked Save Settings with {args.backend_url} / {args.worker_id}.", flush=True)
        print("If Brave asks to allow access to the Back Office host, click Allow.", flush=True)
        await page.click("#save")

        await page.goto(f"{panel_url}#/status", wait_until="domcontentloaded")
        registry_text = ""
        status_text = ""
        deadline = asyncio.get_event_loop().time() + args.wait_seconds
        while asyncio.get_event_loop().time() < deadline:
            registry_text = (await page.text_content("#registryStatus")) or ""
            status_text = (await page.text_content("#status")) or ""
            if "registered (" in registry_text:
                break
            if "BACKEND_PERMISSION_DENIED" in status_text or "BACKEND_PERMISSION_DENIED" in registry_text:
                break
            await asyncio.sleep(1)

        result = {
            "extension_id": extension_id,
            "backend_url": args.backend_url,
            "worker_id": args.worker_id,
            "registry_status": registry_text,
            "status_box": status_text,
            "state": (await page.text_content("#state")) or "",
            "step": (await page.text_content("#step")) or "",
            "backend_worker": backend_worker(args.backend_url, args.worker_id),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
