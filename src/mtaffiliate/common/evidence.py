from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SAFE_QUERY_KEYS = frozenset({"keyword", "page", "shopid", "shop_id", "itemid", "item_id"})


def sanitize_evidence_url(value: str) -> str:
    """Keep only evidence-relevant route/query fields; discard fragments and tracking/auth data."""
    parts = urlsplit(value)
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() in SAFE_QUERY_KEYS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def classify_capture_result(result: dict[str, object]) -> dict[str, str | bool]:
    captcha = bool(result.get("captcha"))
    status = str(result.get("status") or "unknown")
    if captcha:
        return {
            "classification": "BLOCKED_BY_VERIFICATION",
            "blocked": True,
            "promotion_decision": "BLOCK",
        }
    if status == "ok":
        return {
            "classification": "CAPTURED_SUPPORTED_SURFACE",
            "blocked": False,
            "promotion_decision": "HOLD",
        }
    if status == "navigation_error":
        return {
            "classification": "NAVIGATION_ERROR",
            "blocked": False,
            "promotion_decision": "HOLD",
        }
    return {
        "classification": "CAPTURE_INCOMPLETE_OR_UNSUPPORTED",
        "blocked": False,
        "promotion_decision": "HOLD",
    }

PROGRAM1_SEARCH_PROFILE_ID = "shopee-search-lab-v1"
PROGRAM1_SEARCH_PROFILE_VERSION = "1"
PROGRAM1_SEARCH_EVIDENCE_STAGE = "LAB_VALIDATED"


def program1_search_profile_metadata() -> dict[str, str]:
    return {
        "program": "program1",
        "surface": "search",
        "profile_id": PROGRAM1_SEARCH_PROFILE_ID,
        "profile_version": PROGRAM1_SEARCH_PROFILE_VERSION,
        "profile_evidence_stage": PROGRAM1_SEARCH_EVIDENCE_STAGE,
    }


def evaluate_program1_search_evidence_set(
    manifests: list[dict[str, object]],
) -> dict[str, object]:
    """Evaluate structural promotion readiness without inventing live evidence.

    This helper only verifies the evidence package shape/independence. It never
    converts captures into production approval; human/process review under ADR-047
    remains authoritative.
    """
    expected = program1_search_profile_metadata()
    relevant = [
        item
        for item in manifests
        if item.get("profile_id") == expected["profile_id"]
        and item.get("surface") == expected["surface"]
    ]
    supported = [
        item
        for item in relevant
        if item.get("classification") == "CAPTURED_SUPPORTED_SURFACE"
        and not bool(item.get("blocked"))
    ]
    session_ids = {
        str(item.get("capture_session_id"))
        for item in supported
        if item.get("capture_session_id")
    }
    target_urls = {
        str(item.get("target_url"))
        for item in supported
        if item.get("target_url")
    }
    code_versions = {
        str(item.get("code_version"))
        for item in supported
        if item.get("code_version")
    }
    independent = len(session_ids) >= 2 or (
        len(supported) >= 2 and len(target_urls) >= 2
    )
    reasons: list[str] = []
    if len(supported) < 2:
        reasons.append("AT_LEAST_TWO_SUPPORTED_LIVE_CAPTURES_REQUIRED")
    if not independent:
        reasons.append("INDEPENDENT_CAPTURE_DIMENSION_REQUIRED")
    if any(
        item.get("profile_version") != expected["profile_version"]
        or item.get("profile_evidence_stage") != expected["profile_evidence_stage"]
        for item in relevant
    ):
        reasons.append("PROFILE_METADATA_MISMATCH")
    if len(code_versions) > 1:
        reasons.append("CODE_VERSION_MIXED_REVIEW_REQUIRED")

    structurally_ready = not reasons
    return {
        "profile_id": expected["profile_id"],
        "supported_capture_count": len(supported),
        "capture_session_count": len(session_ids),
        "target_url_count": len(target_urls),
        "structurally_ready_for_promotion_review": structurally_ready,
        "promotion_decision": "HOLD" if structurally_ready else "NEEDS_REAL_DATA",
        "reasons": reasons,
        "note": (
            "Structural readiness is not promotion approval; ADR-047 still requires "
            "field-boundary, negative-evidence, fixture/test and senior review gates."
        ),
    }
