from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "docs/affiliate-platform/PROGRAM3_PUBLISHING_SUCCESS_AND_SAFETY_STRATEGY.md",
    "docs/affiliate-platform/PROGRAM3_SYSTEM_ARCHITECTURE.md",
    "docs/affiliate-platform/PROGRAM3_UML_AND_RUNTIME_DIAGRAMS.md",
    "docs/affiliate-platform/PROGRAM3_TRACEABILITY_MATRIX.md",
    "docs/affiliate-platform/PROGRAM3_DEVELOPER_HANDOFF.md",
    "docs/affiliate-platform/PROGRAM3_KANBAN.md",
    "docs/affiliate-platform/PROGRAM3_IMPLEMENTATION_CARDS.md",
    "docs/affiliate-platform/PROGRAM3_AUTOMATED_TEST_ARCHITECTURE.md",
    "src/mtaffiliate/application/program3_authority.py",
    "src/mtaffiliate/application/program3_worker.py",
    "src/mtaffiliate/application/program3_workflow.py",
    "src/mtaffiliate/engines/publishing_guard_engine/service.py",
    "tests/component/test_program3_authority.py",
    "tests/contract/test_program3_authoritative_api.py",
    "tests/integration/sqlite/test_program3_authority_sqlite.py",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, findings: list[str]) -> None:
    if not condition:
        findings.append(message)


def main() -> int:
    findings: list[str] = []
    for path in REQUIRED:
        require((ROOT / path).exists(), f"required Program 3 control missing: {path}", findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    strategy = read(
        "docs/affiliate-platform/PROGRAM3_PUBLISHING_SUCCESS_AND_SAFETY_STRATEGY.md"
    ).lower()
    for token in (
        "program2offerhandoff",
        "post_submitted",
        "blind repost",
        "outcome_unknown",
        "shared job engine",
    ):
        require(token in strategy, f"Program 3 strategy missing semantic control: {token}", findings)

    authority = read("src/mtaffiliate/application/program3_authority.py")
    for token in (
        "Program3OfferHandoff",
        "PUBLISH_CONTENT",
        "validate_active_execution",
        "SUBMISSION_ALREADY_RECORDED",
        "OUTCOME_UNKNOWN",
        "CONFIRMED_FAILURE_SAFE_TO_RETRY",
        "CONFIRMED_SUCCESS",
    ):
        require(token in authority, f"Program 3 authority missing control: {token}", findings)

    worker = read("src/mtaffiliate/application/program3_worker.py")
    for token in (
        "Recognize",
        "destructive_action",
        "CURRENT_SCENE_NOT_CONFIRMED",
        "save_checkpoint",
    ):
        require(token in worker, f"Program 3 Scene worker missing control: {token}", findings)

    api = read("src/mtaffiliate/interfaces/api/app.py")
    for token in (
        "/api/v1/program3/plans",
        "/api/v1/program3/jobs/{publish_job_id}/pre-submit",
        "/api/v1/program3/submissions",
        "/reconcile",
        "/api/v1/program3/publish/confirm",
    ):
        require(token in api, f"Program 3 API contract missing: {token}", findings)

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1

    print(
        "PASS: Program 3 SSOT/runtime/test conformance gate "
        f"({len(REQUIRED)} required control files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
