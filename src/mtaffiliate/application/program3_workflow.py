from __future__ import annotations

from dataclasses import dataclass, field

from mtaffiliate.application.program3_worker import Program3WorkerExecutor, WorkerActionResult
from mtaffiliate.domain.scene.models import SceneSignature
from mtaffiliate.domain.scene.workflow import SceneWorkflow


@dataclass(frozen=True)
class WorkflowRunResult:
    success: bool
    completed_actions: list[str] = field(default_factory=list)
    final_scene: str | None = None
    failure: WorkerActionResult | None = None


class Program3WorkflowRunner:
    """Runs an explicitly planned action sequence through the guarded worker executor."""

    def __init__(self, executor: Program3WorkerExecutor) -> None:
        self._executor = executor

    def run(
        self,
        *,
        publish_job_id: str,
        device_id: str,
        workflow: SceneWorkflow,
        signatures: list[SceneSignature],
        actions: list[str],
        destructive_actions: set[str] | None = None,
    ) -> WorkflowRunResult:
        destructive = destructive_actions or set()
        completed: list[str] = []
        final_scene: str | None = None
        for action_id in actions:
            result = self._executor.execute_action(
                publish_job_id=publish_job_id,
                device_id=device_id,
                workflow=workflow,
                signatures=signatures,
                action_id=action_id,
                destructive_action=action_id in destructive,
            )
            if not result.success:
                return WorkflowRunResult(
                    success=False,
                    completed_actions=completed,
                    final_scene=result.next_scene or result.current_scene,
                    failure=result,
                )
            completed.append(action_id)
            final_scene = result.next_scene
        return WorkflowRunResult(
            success=True,
            completed_actions=completed,
            final_scene=final_scene,
        )
