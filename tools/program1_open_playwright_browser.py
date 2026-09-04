from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / ".browser-profiles" / "shopee-program1"
DEFAULT_EXTENSION = ROOT / "browser_plugin" / "program1"
DEFAULT_URL = "https://shopee.co.th/search?keyword=ssd"
EXTENSION_SCHEME = "chrome-extension://"
KNOWN_BROWSERS = {
    "brave": Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
    "chrome": Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    "edge": Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def default_browser() -> str:
    for name in ("brave", "chrome", "edge"):
        if KNOWN_BROWSERS[name].exists():
            return name
    return "chromium"


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
    parser = argparse.ArgumentParser(
        description="Open a persistent Playwright browser profile for Program 1 Shopee testing."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument(
        "--browser",
        choices=["auto", "brave", "chrome", "edge", "chromium"],
        default="auto",
        help="Browser executable used by Playwright. Auto prefers Brave, then Chrome, then Edge.",
    )
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE))
    parser.add_argument("--extension-dir", default=str(DEFAULT_EXTENSION))
    parser.add_argument(
        "--smoke-close-after",
        type=float,
        default=None,
        help="Close automatically after this many seconds; useful for harness smoke tests.",
    )
    parser.add_argument(
        "--hold",
        action="store_true",
        help="Keep the browser open until this process is interrupted.",
    )
    parser.add_argument(
        "--require-extension",
        action="store_true",
        help="Exit with an error if the Program 1 extension service worker is not loaded.",
    )
    parser.add_argument(
        "--inspect-page",
        action="store_true",
        help="Print compact structured evidence from the opened Shopee page.",
    )
    parser.add_argument(
        "--open-worker-ui",
        action="store_true",
        help="Open the extension worker UI in a normal browser tab for visible testing.",
    )
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir).resolve()
    extension_dir = Path(args.extension_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    if not (extension_dir / "manifest.json").exists():
        raise SystemExit(f"Extension manifest not found: {extension_dir / 'manifest.json'}")

    browser_name = default_browser() if args.browser == "auto" else args.browser
    launch_options = {
        "user_data_dir": str(profile_dir),
        "headless": False,
        "args": [
            f"--disable-extensions-except={extension_dir}",
            f"--load-extension={extension_dir}",
        ],
    }
    if browser_name == "chromium":
        launch_options["channel"] = "chromium"
    else:
        executable_path = KNOWN_BROWSERS[browser_name]
        if not executable_path.exists():
            raise SystemExit(f"Browser executable not found for {browser_name}: {executable_path}")
        launch_options["executable_path"] = str(executable_path)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(**launch_options)
        extension_id = await extension_id_from_context(context)
        if args.require_extension and extension_id is None:
            await context.close()
            raise SystemExit("Program 1 extension service worker was not detected.")
        page = context.pages[0] if context.pages else await context.new_page()
        print(f"Browser: {browser_name}", flush=True)
        print(f"Extension ID: {extension_id or 'not detected'}", flush=True)
        print(f"Opening: {args.url}", flush=True)
        print(f"Persistent profile: {profile_dir}", flush=True)
        try:
            await page.goto(args.url, wait_until="domcontentloaded", timeout=15000)
        except (PlaywrightError, PlaywrightTimeoutError) as error:
            print(f"Navigation did not finish cleanly: {error}", flush=True)
        if args.inspect_page:
            print(json.dumps(await inspect_shopee_page(page), ensure_ascii=False), flush=True)
        if args.open_worker_ui and extension_id:
            worker_ui = await context.new_page()
            await worker_ui.goto(f"{EXTENSION_SCHEME}{extension_id}/src/sidepanel.html")
        if args.smoke_close_after is not None:
            await asyncio.sleep(args.smoke_close_after)
            await context.close()
            return
        if args.hold:
            print("Login/test in the browser window. Stop this process when finished.")
            try:
                while True:
                    await asyncio.sleep(3600)
            finally:
                await context.close()
            return
        print("Login/test in the browser window. Press Enter here when finished.")
        try:
            await asyncio.to_thread(input)
        except EOFError:
            print("No interactive stdin is available; keeping browser open. Stop the process when done.")
            while True:
                await asyncio.sleep(3600)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
