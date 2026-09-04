from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / ".browser-profiles" / "shopee-program1"
DEFAULT_OUT_DIR = ROOT / ".browser-profiles" / "captures"
DEFAULT_URLS = [
    "https://shopee.co.th/search?keyword=ssd&page=1",
    "https://shopee.co.th/search?keyword=keyboard",
]
KNOWN_BROWSERS = {
    "brave": Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
    "chrome": Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    "edge": Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ITEM_ROOT = 'li.shopee-search-item-result__item[data-sqe="item"]'
IDENTITY_RE = r"(?:^|-)i\.\d+\.\d+(?:\?|/|$)"


def default_browser() -> str:
    for name in ("brave", "chrome", "edge"):
        if KNOWN_BROWSERS[name].exists():
            return name
    return "chromium"


async def page_stats(page) -> dict[str, object]:
    return await page.evaluate(
        f"""() => {{
            const root = document.querySelector('div[role="main"]');
            const itemRoot = {json.dumps(ITEM_ROOT)};
            const identityAnchors = [...(root || document).querySelectorAll('a[href]')]
              .filter((anchor) => new RegExp({json.dumps(IDENTITY_RE)}).test(anchor.getAttribute('href') || ''));
            return {{
              url: location.href,
              title: document.title,
              captcha: location.href.includes('/verify/captcha')
                || Boolean(document.querySelector('iframe[src*="captcha"], input[name*="captcha" i]')),
              item_slots: document.querySelectorAll(itemRoot).length,
              hydrated_cards: (root || document).querySelectorAll(itemRoot + ' a[href*="-i."]').length,
              identity_anchor_count: identityAnchors.length,
              sample_hrefs: identityAnchors.slice(0, 3).map((anchor) => anchor.getAttribute('href')),
            }};
          }}"""
    )


async def capture_url(
    context,
    url: str,
    out_dir: Path,
    index: int,
    wait_seconds: float,
) -> dict[str, object]:
    page = await context.new_page()
    slug = re.sub(r"[^a-z0-9]+", "-", url.split("?")[0].rsplit("/", 1)[-1].lower()).strip("-")
    print(f"[{index}] Opening {url}", flush=True)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except (PlaywrightError, PlaywrightTimeoutError) as error:
        print(f"[{index}] Navigation did not finish cleanly: {error}", flush=True)

    deadline = asyncio.get_event_loop().time() + wait_seconds
    result: dict[str, object] = {"status": "timeout", "captcha": False, "captured_at": None}
    navigations = 0
    while True:
        try:
            stats = await page_stats(page)
        except PlaywrightError:
            navigations += 1
            if navigations % 5 == 1:
                print(f"[{index}] Page is mid-navigation; continuing to watch...", flush=True)
            await asyncio.sleep(3)
            continue
        result.update(stats)
        result["captured_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        if not stats["captcha"] and int(stats["hydrated_cards"]) >= 1 and int(stats["identity_anchor_count"]) >= 8:
            print(f"[{index}] Ready (hydrated cards present) — capturing.", flush=True)
            result["status"] = "ok"
            break
        remaining = max(0, int(deadline - asyncio.get_event_loop().time()))
        if stats["captcha"] and remaining % 15 == 0:
            print(
                f"[{index}] CAPTCHA/anti-bot page detected. Solve it in the browser window "
                f"(waiting up to {remaining}s).",
                flush=True,
            )
        if asyncio.get_event_loop().time() >= deadline:
            print(f"[{index}] Timed out waiting for a clean result page.", flush=True)
            break
        await asyncio.sleep(2)

    fragment = ""
    for attempt in range(6):
        try:
            fragment = await page.evaluate(
                """() => {
                    const root = document.querySelector('div[role="main"]');
                    const node = root || document.querySelector('.shopee-search-item-result') || document.body;
                    return node ? node.outerHTML : '';
                  }"""
            )
            break
        except PlaywrightError:
            if attempt < 5:
                await asyncio.sleep(3)
    html_path = out_dir / f"{index:02d}_{slug}_main_fragment.html"
    html_path.write_text(fragment, encoding="utf-8")
    result["html_file"] = str(html_path)
    result["html_bytes"] = len(fragment.encode("utf-8"))
    (out_dir / f"{index:02d}_{slug}_stats.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[{index}] Captured fragment -> {html_path}", flush=True)
    await page.close()
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture sanitized main-fragment DOM evidence from Shopee search pages "
        "using the project owner's logged-in persistent profile. CAPTCHA must be solved by the "
        "human operator in the opened browser window; this tool never bypasses anti-abuse controls."
    )
    parser.add_argument("--urls", nargs="+", default=DEFAULT_URLS)
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE))
    parser.add_argument("--out-dir", default=None, help="Defaults to .browser-profiles/captures/YYYY-MM-DD")
    parser.add_argument("--wait-seconds", type=float, default=240.0)
    parser.add_argument("--browser", choices=["auto", "brave", "chrome", "edge", "chromium"], default="auto")
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir).resolve()
    out_dir = (
        Path(args.out_dir).resolve()
        if args.out_dir
        else DEFAULT_OUT_DIR / datetime.now(UTC).date().isoformat()
    )
    profile_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    browser_name = default_browser() if args.browser == "auto" else args.browser
    launch_options = {"user_data_dir": str(profile_dir), "headless": False, "args": []}
    if browser_name == "chromium":
        launch_options["channel"] = "chromium"
    else:
        executable_path = KNOWN_BROWSERS[browser_name]
        if not executable_path.exists():
            raise SystemExit(f"Browser executable not found for {browser_name}: {executable_path}")
        launch_options["executable_path"] = str(executable_path)

    print(f"Browser: {browser_name}", flush=True)
    print(f"Persistent profile: {profile_dir}", flush=True)
    print(f"Output dir: {out_dir}", flush=True)
    print("If a CAPTCHA appears, solve it in the browser window.", flush=True)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(**launch_options)
        try:
            results = []
            for index, url in enumerate(args.urls, start=1):
                results.append(await capture_url(context, url, out_dir, index, args.wait_seconds))
            summary = out_dir / "summary.json"
            summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Summary -> {summary}", flush=True)
            for result in results:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
