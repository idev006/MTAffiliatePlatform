from mtaffiliate.common.evidence import (
    classify_capture_result,
    evaluate_program1_search_evidence_set,
    program1_search_profile_metadata,
    sanitize_evidence_url,
)


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


def test_program1_search_profile_metadata_matches_runtime_registry() -> None:
    metadata = program1_search_profile_metadata()
    assert metadata == {
        "program": "program1",
        "surface": "search",
        "profile_id": "shopee-search-lab-v1",
        "profile_version": "1",
        "profile_evidence_stage": "LAB_VALIDATED",
    }


def test_search_evidence_set_requires_two_supported_independent_captures() -> None:
    manifest = {
        **program1_search_profile_metadata(),
        "classification": "CAPTURED_SUPPORTED_SURFACE",
        "blocked": False,
        "capture_session_id": "session-a",
        "target_url": "https://shopee.co.th/search?keyword=ssd",
        "code_version": "abc",
    }
    result = evaluate_program1_search_evidence_set([manifest])
    assert result["structurally_ready_for_promotion_review"] is False
    assert result["promotion_decision"] == "NEEDS_REAL_DATA"
    assert "AT_LEAST_TWO_SUPPORTED_LIVE_CAPTURES_REQUIRED" in result["reasons"]


def test_search_evidence_set_accepts_two_independent_supported_captures_for_review_only() -> None:
    base = {
        **program1_search_profile_metadata(),
        "classification": "CAPTURED_SUPPORTED_SURFACE",
        "blocked": False,
        "code_version": "abc",
    }
    result = evaluate_program1_search_evidence_set(
        [
            {
                **base,
                "capture_session_id": "session-a",
                "target_url": "https://shopee.co.th/search?keyword=ssd",
            },
            {
                **base,
                "capture_session_id": "session-b",
                "target_url": "https://shopee.co.th/search?keyword=keyboard",
            },
        ]
    )
    assert result["structurally_ready_for_promotion_review"] is True
    assert result["promotion_decision"] == "HOLD"
    assert result["reasons"] == []


def test_search_evidence_set_rejects_profile_metadata_drift() -> None:
    base = {
        **program1_search_profile_metadata(),
        "classification": "CAPTURED_SUPPORTED_SURFACE",
        "blocked": False,
        "code_version": "abc",
    }
    result = evaluate_program1_search_evidence_set(
        [
            {
                **base,
                "capture_session_id": "session-a",
                "target_url": "https://shopee.co.th/search?keyword=ssd",
            },
            {
                **base,
                "profile_version": "old",
                "capture_session_id": "session-b",
                "target_url": "https://shopee.co.th/search?keyword=keyboard",
            },
        ]
    )
    assert result["structurally_ready_for_promotion_review"] is False
    assert "PROFILE_METADATA_MISMATCH" in result["reasons"]
