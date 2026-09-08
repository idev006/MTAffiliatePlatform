"""Shared local/CI quality gates; scoped PASS never means production approval."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "quality-gates.toml"


def git_output(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True, timeout=10
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "UNAVAILABLE"


def write_report(path: Path, report: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def run_step(command: list[str], cwd: Path, timeout: int, log: Path) -> dict:
    started = time.monotonic()
    result = {"command": command, "cwd": str(cwd), "log": str(log), "status": "FAILED"}
    with log.open("w", encoding="utf-8") as output:
        try:
            completed = subprocess.run(
                command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                timeout=timeout, check=False,
            )
            result["returncode"] = completed.returncode
            result["status"] = "PASS" if completed.returncode == 0 else "FAILED"
        except subprocess.TimeoutExpired:
            result["status"] = "TIMEOUT"
            output.write(f"\nVerification step exceeded {timeout}s.\n")
        except OSError as error:
            result["error"] = str(error)
            output.write(f"\nUnable to start verification step: {error}\n")
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result


def execute(config: dict, selected: list[str], root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    report_path = output / "report.json"
    git_state = git_output(root, "status", "--porcelain")
    versions = {}
    for package in ("ruff", "pytest", "pytest-cov", "playwright"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "NOT_INSTALLED"
    report = {
        "schema_version": 1,
        "started_at": datetime.now(UTC).isoformat(),
        "head": git_output(root, "rev-parse", "HEAD"),
        "branch": git_output(root, "branch", "--show-current"),
        "working_tree_status": git_state,
        "python": sys.executable,
        "python_version": sys.version,
        "tool_versions": versions,
        "selected_stages": selected,
        "status": "RUNNING",
        "full_verification": False,
        "live_brave_shopee_acceptance": "NOT_RUN",
        "stages": [{"name": name, "status": "NOT_RUN", "steps": []} for name in selected],
    }
    write_report(report_path, report)
    try:
        for stage in report["stages"]:
            specification = config["stages"][stage["name"]]
            cwd = (root / specification["cwd"]).resolve()
            cwd.relative_to(root.resolve())
            stage["status"] = "RUNNING"
            write_report(report_path, report)
            for index, template in enumerate(specification["commands"]):
                command = [
                    sys.executable if arg == "{python}" else
                    (shutil.which("node") or "node") if arg == "{node}" else arg
                    for arg in template
                ]
                log = output / f"{stage['name']}-{index + 1}.log"
                print(f"RUN {stage['name']} [{index + 1}] -> {log}", flush=True)
                step = run_step(command, cwd, specification["timeout_seconds"], log)
                stage["steps"].append(step)
                write_report(report_path, report)
                if step["status"] != "PASS":
                    stage["status"] = step["status"]
                    report["status"] = "FAILED"
                    print(log.read_text(encoding="utf-8", errors="replace")[-8000:], flush=True)
                    return report
            stage["status"] = "PASS"
            write_report(report_path, report)
        report["status"] = "PASS"
        report["full_verification"] = selected == config["profiles"]["full"]
        return report
    except KeyboardInterrupt:
        report["status"] = "INTERRUPTED"
        for stage in report["stages"]:
            if stage["status"] == "RUNNING":
                stage["status"] = "INTERRUPTED"
        return report
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["status"] = "FAILED"
        report["error"] = str(error)
        for stage in report["stages"]:
            if stage["status"] == "RUNNING":
                stage["status"] = "FAILED"
        return report
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
        write_report(report_path, report)
        print(f"{report['status']}: {report_path}", flush=True)


def main(argv: list[str] | None = None) -> int:
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--profile", choices=list(config["profiles"]), default="fast")
    selection.add_argument("--stage", choices=list(config["stages"]), action="append")
    parser.add_argument("--list", action="store_true", help="Show commands without running gates")
    args = parser.parse_args(argv)
    selected = args.stage or config["profiles"][args.profile]
    if args.list:
        print(json.dumps({name: config["stages"][name] for name in selected}, indent=2))
        return 0
    if sys.prefix == sys.base_prefix and os.environ.get("GITHUB_ACTIONS") != "true":
        parser.error("Invoke this tool with the approved virtual environment's python executable.")
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    output = ROOT / "runtime" / "verification" / run_id
    report = execute(config, selected, ROOT, output)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
