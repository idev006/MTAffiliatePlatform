from __future__ import annotations

from itertools import pairwise

from mtaffiliate.adapters.android.scripted import ScriptedAndroidAdapter
from mtaffiliate.application.program3_worker import Program3WorkerExecutor
from mtaffiliate.application.program3_workflow import Program3WorkflowRunner
from mtaffiliate.domain.scene.models import SceneEvidence, SceneSignature
from mtaffiliate.domain.scene.workflow import SceneTransition, SceneWorkflow
from mtaffiliate.engines.scene_engine.service import SceneEngine
from mtaffiliate.engines.scene_engine.workflow import SceneWorkflowEngine

SCENES = [
    "VIDEO_SOURCE",
    "VIDEO_PREPARE",
    "PRODUCT_BASKET",
    "POST_DETAILS",
    "READY_TO_PUBLISH",
    "PUBLISHING",
    "PUBLISH_SUCCESS",
]
ACTIONS = [
    "SELECT_VIDEO",
    "CONTINUE_TO_BASKET",
    "ATTACH_PRODUCTS",
    "FILL_DETAILS",
    "SUBMIT_POST",
    "VERIFY_SUCCESS",
]


def signatures() -> list[SceneSignature]:
    return [SceneSignature(scene_id=scene, required_texts={scene}) for scene in SCENES]


def workflow() -> SceneWorkflow:
    return SceneWorkflow(
        workflow_id="full-publish-v1",
        start_scene=SCENES[0],
        terminal_scenes={SCENES[-1]},
        transitions=[
            SceneTransition(from_scene=source, to_scene=target, action_id=action)
            for (source, target), action in zip(pairwise(SCENES), ACTIONS, strict=True)
        ],
    )


def runner(adapter: ScriptedAndroidAdapter) -> Program3WorkflowRunner:
    executor = Program3WorkerExecutor(
        scene_engine=SceneEngine(),
        workflow_engine=SceneWorkflowEngine(),
        ui=adapter,
        evidence=adapter,
        checkpoints=adapter,
    )
    return Program3WorkflowRunner(executor)


def evidence_for_full_success() -> list[SceneEvidence]:
    evidence: list[SceneEvidence] = []
    for source, target in pairwise(SCENES):
        evidence.append(SceneEvidence(texts={source}))
        evidence.append(SceneEvidence(texts={target}))
    return evidence


def test_full_scripted_publish_workflow_reaches_success() -> None:
    adapter = ScriptedAndroidAdapter(evidence_for_full_success())
    result = runner(adapter).run(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        actions=ACTIONS,
        destructive_actions={"SUBMIT_POST"},
    )
    assert result.success
    assert result.completed_actions == ACTIONS
    assert result.final_scene == "PUBLISH_SUCCESS"
    assert len(adapter.checkpoints) == len(ACTIONS)


def test_full_workflow_stops_at_first_unverified_transition() -> None:
    evidence = evidence_for_full_success()
    evidence[5] = SceneEvidence(texts={"UNKNOWN_SCENE"})
    adapter = ScriptedAndroidAdapter(evidence)
    result = runner(adapter).run(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        actions=ACTIONS,
        destructive_actions={"SUBMIT_POST"},
    )
    assert not result.success
    assert result.completed_actions == ACTIONS[:2]
    assert len(adapter.checkpoints) == 2
