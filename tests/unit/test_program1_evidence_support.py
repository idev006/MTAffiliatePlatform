from tools.program1_evidence_support import classify_capture_result, sanitize_evidence_url


def test_sanitize_evidence_url_keeps_only_evidence_relevant_query_fields() -> None:
    value = (
        "https://shopee.co.th/search?keyword=ssd&page=2&session=secret"
        "&utm_source=x#fragment"
    )
    assert sanitize_evidence_url(value) == "https://shopee.co.th/search?keyword=ssd&page=2"


def test_sanitize_evidence_url_preserves_candidate_identity_query_shape() -> None:
    value = "https://shopee.co.th/product?shopid=123&itemid=456&token=secret"
    assert sanitize_evidence_url(value) == "https://shopee.co.th/product?shopid=123&itemid=456"


def test_capture_classification_fails_closed_on_verification() -> None:
    result = classify_capture_result({"status": "timeout", "captcha": True})
    assert result == {
        "classification": "BLOCKED_BY_VERIFICATION",
        "blocked": True,
        "promotion_decision": "BLOCK",
    }


def test_successful_capture_is_hold_not_automatic_promotion() -> None:
    result = classify_capture_result({"status": "ok", "captcha": False})
    assert result["classification"] == "CAPTURED_SUPPORTED_SURFACE"
    assert result["promotion_decision"] == "HOLD"


def test_timeout_without_verification_remains_hold() -> None:
    result = classify_capture_result({"status": "timeout", "captcha": False})
    assert result["classification"] == "CAPTURE_INCOMPLETE_OR_UNSUPPORTED"
    assert result["promotion_decision"] == "HOLD"