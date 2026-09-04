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