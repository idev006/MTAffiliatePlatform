from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from subprocess import Popen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / ".browser-profiles" / "shopee-program1-brave-direct"
DEFAULT_EXTENSION = ROOT / "browser_plugin" / "program1"
DEFAULT_URL = "https://shopee.co.th/search?keyword=ssd"
DEFAULT_DEBUGGING_PORT = 9223
BRAVE_EXE = Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def read_json(url: str) -> object:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_cdp(port: int, timeout_seconds: float = 12) -> bool:
    deadline = time.monotonic() + timeout_seconds
    version_url = f"http://127.0.0.1:{port}/json/version"
    while time.monotonic() < deadline:
        try:
            read_json(version_url)
            return True
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            time.sleep(0.25)
    return False


def open_cdp_tab(port: int, url: str) -> None:
    encoded_url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/json/new?{encoded_url}",
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=5):
        return


def tabs_summary(port: int) -> list[dict[str, object]]:
    tabs = read_json(f"http://127.0.0.1:{port}/json/list")
    if not isinstance(tabs, list):
        return []
    return [
        {
            "title": tab.get("title"),
            "url": tab.get("url"),
            "type": tab.get("type"),
        }
        for tab in tabs
        if isinstance(tab, dict)
    ]


def extension_worker_id(port: int) -> str | None:
    for tab in read_json(f"http://127.0.0.1:{port}/json/list"):
        if not isinstance(tab, dict):
            continue
        url = str(tab.get("url") or "")
        if url.startswith("chrome-extension://") and url.endswith("/src/background.js"):
            return url.split("/")[2]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open Brave directly for Program 1 testing without Playwright."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE))
    parser.add_argument("--extension-dir", default=str(DEFAULT_EXTENSION))
    parser.add_argument("--debugging-port", type=int, default=DEFAULT_DEBUGGING_PORT)
    parser.add_argument("--open-worker-tab", action="store_true")
    args = parser.parse_args()

    if not BRAVE_EXE.exists():
        raise SystemExit(f"Brave executable not found: {BRAVE_EXE}")

    profile_dir = Path(args.profile_dir).resolve()
    extension_dir = Path(args.extension_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    if not (extension_dir / "manifest.json").exists():
        raise SystemExit(f"Extension manifest not found: {extension_dir / 'manifest.json'}")

    command = [
        str(BRAVE_EXE),
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={args.debugging_port}",
        f"--remote-allow-origins=http://127.0.0.1:{args.debugging_port}",
        f"--disable-extensions-except={extension_dir}",
        f"--load-extension={extension_dir}",
        args.url,
    ]
    Popen(command)

    if not wait_for_cdp(args.debugging_port):
        raise SystemExit(f"Brave did not expose CDP on port {args.debugging_port}")

    if args.open_worker_tab:
        extension_id = extension_worker_id(args.debugging_port)
        worker_url = (
            f"chrome-extension://{extension_id}/dist/sidepanel.html#/status"
            if extension_id
            else "chrome://extensions/"
        )
        open_cdp_tab(args.debugging_port, worker_url)

    print("Browser: brave-direct", flush=True)
    print(f"CDP: http://127.0.0.1:{args.debugging_port}", flush=True)
    print(f"Profile: {profile_dir}", flush=True)
    print(f"Extension: {extension_dir}", flush=True)
    print(json.dumps(tabs_summary(args.debugging_port), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
