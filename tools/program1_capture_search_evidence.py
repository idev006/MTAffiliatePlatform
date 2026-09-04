from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from mtaffiliate.common.evidence import classify_capture_result, sanitize_evidence_url

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


def git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        value = result.stdout.strip()
        return value or None
    except (OSError, subprocess.SubprocessError):
        return None


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
    *,
    allow_human_verification_wait: bool,
    browser_name: str,
    session_category: str,
    code_version: str | None,
) -> dict[str, object]:
    page = await context.new_page()
    slug = re.sub(r"[^a-z0-9]+", "-", url.split("?")[0].rsplit("/", 1)[-1].lower()).strip("-")
    print(f"[{index}] Opening {url}", flush=True)
    navigation_error = None
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except (PlaywrightError, PlaywrightTimeoutError) as error:
        navigation_error = str(error)
        print(f"[{index}] Navigation did not finish cleanly: {error}", flush=True)
    try:
        await page.bring_to_front()
    except PlaywrightError:
        pass

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
            if asyncio.get_event_loop().time() >= deadline:
                print(f"[{index}] Timed out while the page kept navigating.", flush=True)
                break
            await asyncio.sleep(3)
            continue
        result.update(stats)
        result["captured_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        if not stats["captcha"] and int(stats["hydrated_cards"]) >= 1 and int(stats["identity_anchor_count"]) >= 8:
            print(f"[{index}] Ready (hydrated cards present) — capturing.", flush=True)
            result["status"] = "ok"
            break
        remaining = max(0, int(deadline - asyncio.get_event_loop().time()))
        if stats["captcha"]:
            if not allow_human_verification_wait:
                print(
                    f"[{index}] Verification/anti-bot boundary detected; recording BLOCKED and stopping this capture.",
                    flush=True,
                )
                result["status"] = "blocked"
                break
            if remaining % 15 == 0:
                print(
                    f"[{index}] Verification boundary detected. Human verification wait is explicitly enabled "
                    f"(remaining {remaining}s).",
                    flush=True,
                )
            try:
                await page.bring_to_front()
            except PlaywrightError:
                pass
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
                    if (!node) return '';
                    const clone = node.cloneNode(true);
                    clone.querySelectorAll('script, style, iframe, noscript').forEach((item) => item.remove());
                    clone.querySelectorAll('input, textarea').forEach((item) => {
                      item.removeAttribute('value');
                      if ('value' in item) item.value = '';
                    });
                    const secretName = /(token|session|cookie|auth|csrf|nonce|user.?id|account.?id)/i;
                    clone.querySelectorAll('*').forEach((element) => {
                      [...element.attributes].forEach((attr) => {
                        const name = attr.name;
                        if (secretName.test(name)) {
                          element.removeAttribute(name);
                          return;
                        }
                        if (name === 'src' || name === 'srcset') {
                          element.removeAttribute(name);
                          return;
                        }
                        if (name === 'href' || name === 'action') {
                          try {
                            const parsed = new URL(attr.value, location.href);
                            const keep = new URL(parsed.origin + parsed.pathname);
                            for (const key of ['keyword', 'page', 'shopid', 'shop_id', 'itemid', 'item_id']) {
                              const value = parsed.searchParams.get(key);
                              if (value !== null) keep.searchParams.set(key, value);
                            }
                            element.setAttribute(name, keep.href);
                          } catch (_error) {
                            element.removeAttribute(name);
                          }
                        }
                      });
                    });
                    return clone.outerHTML;
                  }"""
            )
            break
        except PlaywrightError:
            if attempt < 5:
                await asyncio.sleep(3)
    html_path = out_dir / f"{index:02d}_{slug}_main_fragment.html"
    html_path.write_text(fragment, encoding="utf-8")
    digest = hashlib.sha256(fragment.encode("utf-8")).hexdigest()
    classification = classify_capture_result(result)
    safe_url = sanitize_evidence_url(str(result.get("url") or url))
    try:
        user_agent = await page.evaluate("() => navigator.userAgent")
    except PlaywrightError:
        user_agent = None
    manifest = {
        "evidence_id": f"p1-live-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{index:02d}",
        "captured_at": result.get("captured_at") or datetime.now(UTC).isoformat(timespec="seconds"),
        "program": "program1",
        "surface": "search",
        "profile": "shopee-current-page-lab-v2",
        "target_url": sanitize_evidence_url(url),
        "observed_url": safe_url,
        "browser": browser_name,
        "browser_user_agent": user_agent,
        "session_category": session_category,
        "collection_method": "headed_playwright_persistent_context",
        "code_version": code_version,
        "classification": classification["classification"],
        "blocked": classification["blocked"],
        "promotion_decision": classification["promotion_decision"],
        "captcha_or_verification_detected": bool(result.get("captcha")),
        "item_slots": result.get("item_slots"),
        "hydrated_cards": result.get("hydrated_cards"),
        "identity_anchor_count": result.get("identity_anchor_count"),
        "sample_hrefs": [
            sanitize_evidence_url(str(value))
            for value in (result.get("sample_hrefs") or [])
            if value
        ],
        "navigation_error": navigation_error,
        "sanitized_html_file": html_path.name,
        "sanitized_html_sha256": digest,
        "sanitized_html_bytes": len(fragment.encode("utf-8")),
        "sanitization": [
            "scripts/styles/iframes/noscript removed",
            "input/textarea values removed",
            "media src/srcset removed",
            "secret-like attributes removed",
            "URLs reduced to route plus evidence-relevant query fields",
            "cookies/tokens are never exported by this tool",
        ],
        "limitations": [
            "capture alone never promotes a profile",
            "field semantics still require repeated independent evidence",
            "logged-in platform output may remain personalized even after structural sanitization",
        ],
    }
    manifest_path = out_dir / f"{index:02d}_{slug}_evidence_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    result["html_file"] = str(html_path)
    result["html_bytes"] = len(fragment.encode("utf-8"))
    result["manifest_file"] = str(manifest_path)
    result.update(classification)
    (out_dir / f"{index:02d}_{slug}_stats.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[{index}] Sanitized fragment -> {html_path}", flush=True)
    print(f"[{index}] Evidence manifest -> {manifest_path}", flush=True)
    await page.close()
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture structurally sanitized DOM evidence plus an evidence manifest from "
        "authorized Shopee search sessions. Verification/anti-bot boundaries fail closed by default; "
        "the tool never bypasses anti-abuse controls."
    )
    parser.add_argument("--urls", nargs="+", default=DEFAULT_URLS)
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE))
    parser.add_argument("--out-dir", default=None, help="Defaults to .browser-profiles/captures/YYYY-MM-DD")
    parser.add_argument("--wait-seconds", type=float, default=240.0)
    parser.add_argument("--browser", choices=["auto", "brave", "chrome", "edge", "chromium"], default="auto")
    parser.add_argument(
        "--session-category",
        default="authorized-persistent-profile",
        help="Non-secret evidence label only; do not put account identifiers or tokens here.",
    )
    parser.add_argument(
        "--allow-human-verification-wait",
        action="store_true",
        help="Explicitly allow the tool to wait while a human completes a platform verification step. "
        "The tool never solves or bypasses verification itself.",
    )
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
    if args.allow_human_verification_wait:
        print("Human verification wait explicitly enabled; the tool itself never solves/bypasses it.", flush=True)
    else:
        print("Verification/anti-bot pages fail closed immediately.", flush=True)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(**launch_options)
        try:
            results = []
            for index, url in enumerate(args.urls, start=1):
                results.append(
                    await capture_url(
                        context,
                        url,
                        out_dir,
                        index,
                        args.wait_seconds,
                        allow_human_verification_wait=args.allow_human_verification_wait,
                        browser_name=browser_name,
                        session_category=args.session_category,
                        code_version=git_head(),
                    )
                )
            summary = out_dir / "summary.json"
            summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Summary -> {summary}", flush=True)
            for result in results:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
