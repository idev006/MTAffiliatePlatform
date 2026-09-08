from __future__ import annotations

import importlib.util
import json
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("program1_verify", ROOT / "tools/program1_verify.py")
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


def registry(first: str, second: str = "print('second')") -> dict:
    return {
        "profiles": {"full": ["first", "second"]},
        "stages": {
            name: {"cwd": ".", "timeout_seconds": 10,
                   "commands": [["{python}", "-c", code]]}
            for name, code in (("first", first), ("second", second))
        },
    }


def test_failure_preserves_logs_and_does_not_run_later_steps(tmp_path):
    config = registry("print('diagnostic', flush=True); raise SystemExit(7)")
    output = tmp_path / "report"
    result = verify.execute(config, ["first", "second"], tmp_path, output)
    assert result["status"] == "FAILED"
    assert result["stages"][0]["steps"][0]["returncode"] == 7
    assert result["stages"][1]["status"] == "NOT_RUN"
    assert not result["full_verification"]
    assert "diagnostic" in (output / "first-1.log").read_text()
    assert json.loads((output / "report.json").read_text()) == result


def test_scoped_success_uses_invoked_python_and_explicit_cwd(tmp_path, monkeypatch):
    working = tmp_path / "repository"
    working.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    config = registry("from pathlib import Path; print(Path.cwd())")
    output = tmp_path / "report"
    result = verify.execute(config, ["first"], working, output)
    assert result["status"] == "PASS"
    assert not result["full_verification"]
    assert result["python"] == sys.executable
    assert str(working) in (output / "first-1.log").read_text()
    assert result["live_brave_shopee_acceptance"] == "NOT_RUN"


def test_full_success_only_after_every_gate(tmp_path):
    result = verify.execute(registry("print('first')"), ["first", "second"], tmp_path,
                            tmp_path / "report")
    assert result["status"] == "PASS"
    assert result["full_verification"]


def test_timeout_fails_and_report_survives(tmp_path):
    config = registry("import time; time.sleep(20)")
    config["stages"]["first"]["timeout_seconds"] = 1
    result = verify.execute(config, ["first", "second"], tmp_path, tmp_path / "report")
    assert result["status"] == "FAILED"
    assert result["stages"][0]["status"] == "TIMEOUT"
    assert result["stages"][1]["status"] == "NOT_RUN"


def test_missing_executable_is_a_failed_step(tmp_path):
    result = verify.run_step([str(tmp_path / "absent-executable")], tmp_path, 2,
                             tmp_path / "missing.log")
    assert result["status"] == "FAILED"
    assert "error" in result


def test_interruption_keeps_evidence_and_blocks_full_pass(tmp_path, monkeypatch):
    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(verify, "run_step", interrupt)
    output = tmp_path / "report"
    result = verify.execute(registry("print('first')"), ["first", "second"], tmp_path, output)
    assert result["status"] == "INTERRUPTED"
    assert result["stages"][0]["status"] == "INTERRUPTED"
    assert result["stages"][1]["status"] == "NOT_RUN"
    assert not result["full_verification"]
    assert json.loads((output / "report.json").read_text()) == result


def test_local_system_python_is_rejected_without_fallback(monkeypatch):
    monkeypatch.setattr(sys, "prefix", sys.base_prefix)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(SystemExit) as error:
        verify.main(["--stage", "core"])
    assert error.value.code == 2


def test_registry_preserves_required_gate_layers_and_coverage():
    config = tomllib.loads(verify.CONFIG.read_text())
    assert config["profiles"]["full"] == [
        "static", "core", "sqlite", "stress", "extension", "browser",
    ]
    for name in ("core", "sqlite"):
        command = config["stages"][name]["commands"][0]
        assert command[:3] == ["{python}", "-m", "pytest"]
        assert "--cov-branch" in command
        assert "--cov-fail-under=95" in command
