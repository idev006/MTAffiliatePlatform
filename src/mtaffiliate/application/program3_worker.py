from __future__ import annotations

from dataclasses import dataclass

from mtaffiliate.domain.scene.models import SceneSignature
from mtaffiliate.domain.scene.workflow import RecoveryDecision, SceneWorkflow
from mtaffiliate.engines.scene_engine.service import SceneEngine
from mtaffiliate.engines.scene_engine.workflow import SceneWorkflowEngine
from mtaffiliate.ports.android import CheckpointPort, SceneEvidencePort, UIAutomationPort


@dataclass(frozen=True)
class WorkerActionResult:
    success: bool
    current_scene: str | None
    next_scene: str | None
    reason: str
    recovery: RecoveryDecision | None = None


class Program3WorkerExecutor:
    """Headless Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint executor."""

    def __init__(
        self,
        *,
        scene_engine: SceneEngine,
        workflow_engine: SceneWorkflowEngine,
        ui: UIAutomationPort,
        evidence: SceneEvidencePort,
        checkpoints: CheckpointPort,
    ) -> None:
        self._scene_engine = scene_engine
        self._workflow_engine = workflow_engine
        self._ui = ui
        self._evidence = evidence
        self._checkpoints = checkpoints

    def execute_action(
        self,
        *,
        publish_job_id: str,
        device_id: str,
        workflow: SceneWorkflow,
        signatures: list[SceneSignature],
        action_id: str,
        destructive_action: bool = False,
    ) -> WorkerActionResult:
        before = self._scene_engine.recognize(self._evidence.capture(device_id), signatures)
        if before.status != "CONFIRMED" or before.scene_id is None:
            recovery = self._workflow_engine.recovery_for(
                before,
                destructive_action_submitted=False,
                failed_attempts=0,
            )
            return WorkerActionResult(
                success=False,
                current_scene=before.scene_id,
                next_scene=None,
                reason="CURRENT_SCENE_NOT_CONFIRMED",
                recovery=recovery,
            )

        transition = self._workflow_engine.validate_action(
            workflow,
            current_scene=before.scene_id,
            action_id=action_id,
        )
        if not transition.allowed or transition.expected_scene is None:
            return WorkerActionResult(
                success=False,
                current_scene=before.scene_id,
                next_scene=None,
                reason=transition.reason,
            )

        self._ui.perform_action(device_id, action_id)
        after = self._scene_engine.recognize(self._evidence.capture(device_id), signatures)
        verified = self._workflow_engine.verify_transition(transition.expected_scene, after)
        if not verified.allowed:
            recovery = self._workflow_engine.recovery_for(
                after,
                destructive_action_submitted=destructive_action,
                failed_attempts=1,
            )
            return WorkerActionResult(
                success=False,
                current_scene=before.scene_id,
                next_scene=after.scene_id,
                reason=verified.reason,
                recovery=recovery,
            )

        self._checkpoints.save_checkpoint(
            publish_job_id,
            transition.expected_scene,
            action_id,
        )
        return WorkerActionResult(
            success=True,
            current_scene=before.scene_id,
            next_scene=transition.expected_scene,
            reason="ACTION_VERIFIED_AND_CHECKPOINTED",
        )
