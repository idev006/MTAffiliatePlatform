from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/affiliate-platform/PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md",
    "docs/affiliate-platform/WORKFLOW.md",
    "docs/affiliate-platform/APPLICATION_AND_ENGINE_CONTRACTS.md",
    "docs/affiliate-platform/TEST_STRATEGY_AND_QUALITY_GATES.md",
    "docs/affiliate-platform/SYSTEM_PHYSIOLOGY_MODEL.md",
    "docs/affiliate-platform/COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md",
    "browser_plugin/program1/src/background.js",
    "browser_plugin/program1/src/job_lifecycle.mjs",
    "browser_plugin/program1/src/background_execution.mjs",
    "tests/integration/sqlite/test_program1_world_class_simulation.py",
)

REQUIRED_BACKGROUND_TOKENS = (
    "createProgram1JobLifecycle",
    "PROGRAM1_LEASE_NEXT_JOB",
    "PROGRAM1_RENEW_ACTIVE_JOB",
    "PROGRAM1_RECONCILE_ACTIVE_JOB",
    "PROGRAM1_COMPLETE_ACTIVE_JOB",
    "PROGRAM1_START_BACKGROUND_RUN",
    "PROGRAM1_STOP_BACKGROUND_RUN",
    "PROGRAM1_RUN_BACKGROUND_CYCLE",
    "AUTO_RUN_ALARM",
    "OBSERVATION_BATCH_ACK",
)

REQUIRED_WORKFLOW_TOKENS = (
    "Affiliate / Marketing Strategy",
    "Product Discovery Worker leases bounded work",
    "Product identity is normalized/deduplicated",
    "historical observations are preserved rather than overwritten",
    "Qualification / Explainable Ranking",
    "Shared Job Engine is lifecycle SSOT",
)

REQUIRED_STRATEGY_TOKENS = (
    "Which product opportunities should we pursue next",
    "Strategy Leads Engineering",
    "Opportunity Thesis",
    "Historical Observation Is Required",
    "Evidence-First Policy",
    "North-Star Outcomes",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, findings: list[str]) -> None:
    if not condition:
        findings.append(message)


def main() -> int:
    findings: list[str] = []

    for relative in REQUIRED_FILES:
        require((ROOT / relative).is_file(), f"missing required SSOT/control file: {relative}", findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    manifest = json.loads(read("browser_plugin/program1/manifest.json"))
    package = json.loads(read("browser_plugin/program1/package.json"))
    package_lock = json.loads(read("browser_plugin/program1/package-lock.json"))
    readme = read("browser_plugin/program1/README.md")

    versions = {
        "manifest": manifest["version"],
        "package": package["version"],
        "package-lock": package_lock["version"],
    }
    require(
        len(set(versions.values())) == 1,
        f"Program 1 extension version drift: {versions}",
        findings,
    )
    version = manifest["version"]
    require(
        f"Current extension version: `{version}`." in readme,
        f"README extension version does not match {version}",
        findings,
    )

    background = read("browser_plugin/program1/src/background.js")
    for token in REQUIRED_BACKGROUND_TOKENS:
        require(token in background, f"background lifecycle contract missing token: {token}", findings)

    workflow = read("docs/affiliate-platform/WORKFLOW.md")
    for token in REQUIRED_WORKFLOW_TOKENS:
        require(token in workflow, f"workflow governing token missing: {token}", findings)

    strategy = read("docs/affiliate-platform/PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md")
    for token in REQUIRED_STRATEGY_TOKENS:
        require(token in strategy, f"strategy governing token missing: {token}", findings)

    contracts = read("docs/affiliate-platform/APPLICATION_AND_ENGINE_CONTRACTS.md")
    require(
        "DeriveOpportunityFeatures" in contracts and "EvaluateOpportunity" in contracts,
        "Program 1 opportunity contracts are missing",
        findings,
    )

    simulation = read("tests/integration/sqlite/test_program1_world_class_simulation.py")
    for token in ("survives_restart", "NEEDS_HUMAN", "batch_id_reuse", "idempotent"):
        require(token in simulation, f"simulation control missing scenario token: {token}", findings)

    job_lifecycle = read("browser_plugin/program1/src/job_lifecycle.mjs")
    for token in ("leaseAndStart", "renew", "checkpoint", "verifyAndComplete", "reconcile"):
        require(
            re.search(rf"\b{re.escape(token)}\b", job_lifecycle) is not None,
            f"background lifecycle controller missing operation: {token}",
            findings,
        )

    execution = read("browser_plugin/program1/src/background_execution.mjs")
    for token in (
        "collection_targets",
        "scheduleWake",
        "runOneCycle",
        "resumeAfterWake",
        "PAGINATION_NEXT_URL_MISSING",
    ):
        require(
            token in execution,
            f"background execution control missing token: {token}",
            findings,
        )

    panel = read("browser_plugin/program1/src/ui/stores/process.js")
    require(
        "PROGRAM1_START_BACKGROUND_RUN" in panel
        and "PROGRAM1_STOP_BACKGROUND_RUN" in panel,
        "Side Panel must command the background runtime for auto execution",
        findings,
    )

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print(
        "PASS: Program 1 SSOT/runtime/test conformance gate "
        f"(extension {version}, {len(REQUIRED_FILES)} required control files)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
