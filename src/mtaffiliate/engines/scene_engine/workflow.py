from __future__ import annotations

from mtaffiliate.domain.scene.models import SceneRecognition
from mtaffiliate.domain.scene.workflow import (
    RecoveryDecision,
    SceneWorkflow,
    TransitionDecision,
)


class SceneWorkflowEngine:
    """Pure workflow/transition guard for scene-aware execution."""

    def validate_action(
        self,
        workflow: SceneWorkflow,
        *,
        current_scene: str,
        action_id: str,
    ) -> TransitionDecision:
        matches = [
            transition
            for transition in workflow.transitions
            if transition.from_scene == current_scene and transition.action_id == action_id
        ]
        if not matches:
            return TransitionDecision(allowed=False, reason="ACTION_NOT_ALLOWED_IN_SCENE")
        if len(matches) > 1:
            return TransitionDecision(allowed=False, reason="AMBIGUOUS_WORKFLOW_TRANSITION")
        return TransitionDecision(
            allowed=True,
            reason="TRANSITION_ALLOWED",
            expected_scene=matches[0].to_scene,
        )

    def verify_transition(
        self,
        expected_scene: str,
        observed: SceneRecognition,
    ) -> TransitionDecision:
        if observed.status != "CONFIRMED":
            return TransitionDecision(
                allowed=False,
                reason="NEXT_SCENE_NOT_CONFIRMED",
                expected_scene=expected_scene,
            )
        if observed.scene_id != expected_scene:
            return TransitionDecision(
                allowed=False,
                reason="UNEXPECTED_NEXT_SCENE",
                expected_scene=expected_scene,
            )
        return TransitionDecision(
            allowed=True,
            reason="EXPECTED_SCENE_CONFIRMED",
            expected_scene=expected_scene,
        )

    def recovery_for(
        self,
        observed: SceneRecognition,
        *,
        destructive_action_submitted: bool,
        failed_attempts: int,
    ) -> RecoveryDecision:
        if destructive_action_submitted:
            return RecoveryDecision(
                level="NEEDS_HUMAN",
                reason="POST_SUBMITTED_OUTCOME_MUST_BE_RECONCILED",
            )
        if observed.status in {"UNKNOWN", "AMBIGUOUS"} and failed_attempts == 0:
            return RecoveryDecision(level="REOBSERVE", reason="SCENE_NOT_STABLE")
        if failed_attempts <= 1:
            return RecoveryDecision(level="LOCAL", reason="TRY_LOCAL_SAFE_RECOVERY")
        if failed_attempts == 2:
            return RecoveryDecision(level="SAFE_ANCHOR", reason="RETURN_TO_SAFE_ANCHOR")
        if failed_attempts == 3:
            return RecoveryDecision(level="RESTART", reason="CONTROLLED_APP_RESTART")
        return RecoveryDecision(level="NEEDS_HUMAN", reason="RECOVERY_BUDGET_EXHAUSTED")
