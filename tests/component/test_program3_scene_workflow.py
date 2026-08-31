from __future__ import annotations

import pytest

from mtaffiliate.domain.scene.models import SceneRecognition
from mtaffiliate.domain.scene.workflow import SceneTransition, SceneWorkflow
from mtaffiliate.engines.scene_engine.workflow import SceneWorkflowEngine


def workflow() -> SceneWorkflow:
    return SceneWorkflow(
        workflow_id="publish-v1",
        start_scene="VIDEO_SOURCE",
        terminal_scenes={"PUBLISH_SUCCESS"},
        transitions=[
            SceneTransition(
                from_scene="VIDEO_SOURCE",
                to_scene="VIDEO_PREPARE",
                action_id="SELECT_VIDEO",
            ),
            SceneTransition(
                from_scene="VIDEO_PREPARE",
                to_scene="PRODUCT_BASKET",
                action_id="CONTINUE",
            ),
            SceneTransition(
                from_scene="READY_TO_PUBLISH",
                to_scene="PUBLISHING",
                action_id="SUBMIT_POST",
            ),
            SceneTransition(
                from_scene="PUBLISHING",
                to_scene="PUBLISH_SUCCESS",
                action_id="VERIFY_SUCCESS",
            ),
        ],
    )


def test_action_must_be_allowed_in_current_scene() -> None:
    engine = SceneWorkflowEngine()
    allowed = engine.validate_action(
        workflow(),
        current_scene="VIDEO_SOURCE",
        action_id="SELECT_VIDEO",
    )
    assert allowed.allowed
    assert allowed.expected_scene == "VIDEO_PREPARE"

    blocked = engine.validate_action(
        workflow(),
        current_scene="VIDEO_SOURCE",
        action_id="SUBMIT_POST",
    )
    assert not blocked.allowed
    assert blocked.reason == "ACTION_NOT_ALLOWED_IN_SCENE"


def test_transition_requires_confirmed_expected_scene() -> None:
    engine = SceneWorkflowEngine()
    assert engine.verify_transition(
        "PRODUCT_BASKET",
        SceneRecognition(scene_id="PRODUCT_BASKET", status="CONFIRMED"),
    ).allowed
    assert not engine.verify_transition(
        "PRODUCT_BASKET",
        SceneRecognition(status="UNKNOWN"),
    ).allowed
    mismatch = engine.verify_transition(
        "PRODUCT_BASKET",
        SceneRecognition(scene_id="POST_DETAILS", status="CONFIRMED"),
    )
    assert not mismatch.allowed
    assert mismatch.reason == "UNEXPECTED_NEXT_SCENE"


@pytest.mark.parametrize(
    ("attempts", "level"),
    [(0, "REOBSERVE"), (1, "LOCAL"), (2, "SAFE_ANCHOR"), (3, "RESTART"), (4, "NEEDS_HUMAN")],
)
def test_recovery_is_bounded(attempts: int, level: str) -> None:
    engine = SceneWorkflowEngine()
    decision = engine.recovery_for(
        SceneRecognition(status="UNKNOWN"),
        destructive_action_submitted=False,
        failed_attempts=attempts,
    )
    assert decision.level == level


def test_post_submitted_uncertainty_never_restarts_or_reposts() -> None:
    engine = SceneWorkflowEngine()
    decision = engine.recovery_for(
        SceneRecognition(status="UNKNOWN"),
        destructive_action_submitted=True,
        failed_attempts=0,
    )
    assert decision.level == "NEEDS_HUMAN"
    assert "RECONCILED" in decision.reason
