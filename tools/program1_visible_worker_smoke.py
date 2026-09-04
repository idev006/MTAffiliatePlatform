from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / ".browser-profiles" / "shopee-program1-visible"
EXTENSION_DIR = ROOT / "browser_plugin" / "program1"
BRAVE_EXE = Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")
SHOPEE_URL = "https://shopee.co.th/search?keyword=ssd"
WORKER_ID = "worker-01"
BACKEND_URL = "http://127.0.0.1:8000"
EXTENSION_SCHEME = "chrome-extension://"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


async def extension_id_from_context(context) -> str | None:
    service_worker = next(iter(context.service_workers), None)
    if service_worker is None:
        try:
            service_worker = await asyncio.wait_for(context.wait_for_event("serviceworker"), 8)
        except TimeoutError:
            return None
    if not service_worker.url.startswith(EXTENSION_SCHEME):
        return None
    return service_worker.url.removeprefix(EXTENSION_SCHEME).split("/", maxsplit=1)[0]


async def inspect_shopee_page(page) -> dict[str, object]:
    return await page.evaluate(
        """() => {
          const identityAnchors = [...document.querySelectorAll('a[href]')]
            .filter((anchor) => /(?:^|-)i\\.\\d+\\.\\d+(?:\\?|\\/|$)/.test(anchor.getAttribute('href') || ''));
          return {
            url: location.href,
            title: document.title,
            captcha: location.href.includes('/verify/captcha') || Boolean(document.querySelector('iframe[src*="captcha"], input[name*="captcha" i]')),
            search_item_count: document.querySelectorAll('li.shopee-search-item-result__item[data-sqe="item"]').length,
            identity_anchor_count: identityAnchors.length,
            sample_hrefs: identityAnchors.slice(0, 3).map((anchor) => anchor.getAttribute('href')),
          };
        }"""
    )


async def main() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if not BRAVE_EXE.exists():
        raise SystemExit(f"Brave executable not found: {BRAVE_EXE}")
    if not (EXTENSION_DIR / "manifest.json").exists():
        raise SystemExit(f"Extension manifest not found: {EXTENSION_DIR / 'manifest.json'}")

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=str(BRAVE_EXE),
            headless=False,
            args=[
                f"--disable-extensions-except={EXTENSION_DIR}",
                f"--load-extension={EXTENSION_DIR}",
            ],
        )
        extension_id = await extension_id_from_context(context)
        if extension_id is None:
            await context.close()
            raise SystemExit("Program 1 extension service worker was not detected.")

        shopee = context.pages[0] if context.pages else await context.new_page()
        try:
            await shopee.goto(SHOPEE_URL, wait_until="domcontentloaded", timeout=15000)
        except (PlaywrightError, PlaywrightTimeoutError) as error:
            print(f"Shopee navigation did not finish cleanly: {error}", flush=True)
        await shopee.bring_to_front()
        await asyncio.sleep(5)
        print(json.dumps(await inspect_shopee_page(shopee), ensure_ascii=False), flush=True)

        worker = await context.new_page()
        await worker.goto(f"{EXTENSION_SCHEME}{extension_id}/src/sidepanel.html")
        await worker.fill("#backendUrl", BACKEND_URL)
        await worker.fill("#workerId", WORKER_ID)
        await worker.fill("#targetUrl", SHOPEE_URL)
        await worker.evaluate(
            """() => {
              document.querySelector('#delayMinSeconds').value = '0';
              document.querySelector('#delayMaxSeconds').value = '600';
              document.querySelector('#delayMinSeconds').dispatchEvent(new Event('input', { bubbles: true }));
              document.querySelector('#delayMaxSeconds').dispatchEvent(new Event('input', { bubbles: true }));
            }"""
        )
        await worker.bring_to_front()
        print(f"Worker UI: {EXTENSION_SCHEME}{extension_id}/src/sidepanel.html", flush=True)
        print(f"Backend URL set in UI: {BACKEND_URL}", flush=True)
        print("Click Save Settings, allow permissions if prompted, then Start Auto Run.", flush=True)
        print("Browser remains open for visible testing. Stop this process when done.", flush=True)
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
