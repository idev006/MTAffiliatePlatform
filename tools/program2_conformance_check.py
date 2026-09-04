from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "docs/affiliate-platform/PROGRAM2_AFFILIATE_SUCCESS_STRATEGY.md",
    "docs/affiliate-platform/PROGRAM2_SYSTEM_ARCHITECTURE.md",
    "docs/affiliate-platform/PROGRAM2_UML_AND_RUNTIME_DIAGRAMS.md",
    "docs/affiliate-platform/PROGRAM2_TRACEABILITY_MATRIX.md",
    "docs/affiliate-platform/PROGRAM2_DEVELOPER_HANDOFF.md",
    "docs/affiliate-platform/PROGRAM2_KANBAN.md",
    "docs/affiliate-platform/PROGRAM2_IMPLEMENTATION_CARDS.md",
    "docs/affiliate-platform/PROGRAM2_AUTOMATED_TEST_ARCHITECTURE.md",
    "src/mtaffiliate/application/program2_jobs.py",
    "src/mtaffiliate/application/program2_intelligence.py",
    "src/mtaffiliate/application/program2_artifacts.py",
    "src/mtaffiliate/engines/affiliate_offer_engine/service.py",
    "tests/contract/test_program2_authoritative_flow.py",
    "tests/integration/sqlite/test_program2_authoritative_sqlite.py",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, findings: list[str]) -> None:
    if not condition:
        findings.append(message)


def main() -> int:
    findings: list[str] = []
    for path in REQUIRED:
        require((ROOT / path).exists(), f"required Program 2 control missing: {path}", findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    strategy = read("docs/affiliate-platform/PROGRAM2_AFFILIATE_SUCCESS_STRATEGY.md")
    strategy_lower = strategy.lower()
    for token in (
        "qualifiedopportunityhandoff",
        "preferred + backups",
        "freshness",
        "program3",
        "needs_human",
    ):
        require(
            token in strategy_lower,
            f"Program 2 strategy missing semantic control: {token}",
            findings,
        )

    architecture = read("docs/affiliate-platform/PROGRAM2_SYSTEM_ARCHITECTURE.md")
    for token in (
        "Shared Job Engine",
        "Offer Feature",
        "Durable Selection Decision",
        "Program3 Ready Handoff",
        "UI closure",
    ):
        require(token in architecture, f"Program 2 architecture missing control: {token}", findings)

    jobs = read("src/mtaffiliate/application/program2_jobs.py")
    for token in (
        "QualifiedOpportunityHandoff",
        "TEST_NOW",
        "DISCOVER_AFFILIATE_OFFERS",
        "canonical_product_id",
        "get_work_package",
    ):
        require(token in jobs, f"Program 2 job authority missing token: {token}", findings)

    api = read("src/mtaffiliate/interfaces/api/app.py")
    for token in (
        "job-bound offer observations require job_id, worker_id and lease_token",
        "validate_active_execution",
        "offer observation product/account does not match work package",
        "session_context_id",
        "selection-decisions",
        "program3-handoff",
    ):
        require(token in api, f"Program 2 API/provenance control missing: {token}", findings)

    intelligence = read("src/mtaffiliate/application/program2_intelligence.py")
    for token in (
        "source_job_id",
        "OfferSelectionDecision",
        "evidence_refs",
        "program2-selection-lab-v1",
    ):
        require(token in intelligence, f"Program 2 decision traceability missing: {token}", findings)

    artifacts = read("src/mtaffiliate/application/program2_artifacts.py")
    for token in (
        "selection is stale",
        "validation_state",
        "Program3OfferHandoff",
        "source_job_id",
    ):
        require(token in artifacts, f"Program 2 handoff gate missing: {token}", findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print(
        "PASS: Program 2 SSOT/runtime/test conformance gate "
        f"({len(REQUIRED)} required control files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
