from __future__ import annotations

from mtaffiliate.adapters.android.scripted import ScriptedAndroidAdapter
from mtaffiliate.application.program3_worker import Program3WorkerExecutor
from mtaffiliate.domain.scene.models import SceneEvidence, SceneSignature
from mtaffiliate.domain.scene.workflow import SceneTransition, SceneWorkflow
from mtaffiliate.engines.scene_engine.service import SceneEngine
from mtaffiliate.engines.scene_engine.workflow import SceneWorkflowEngine


def signatures() -> list[SceneSignature]:
    return [
        SceneSignature(scene_id="VIDEO_SOURCE", required_texts={"Choose video"}),
        SceneSignature(scene_id="VIDEO_PREPARE", required_texts={"Continue"}),
        SceneSignature(scene_id="PUBLISHING", required_texts={"Publishing"}),
    ]


def workflow() -> SceneWorkflow:
    return SceneWorkflow(
        workflow_id="publish-v1",
        start_scene="VIDEO_SOURCE",
        terminal_scenes={"PUBLISHING"},
        transitions=[
            SceneTransition(
                from_scene="VIDEO_SOURCE",
                to_scene="VIDEO_PREPARE",
                action_id="SELECT_VIDEO",
            ),
            SceneTransition(
                from_scene="VIDEO_PREPARE",
                to_scene="PUBLISHING",
                action_id="SUBMIT_POST",
            ),
        ],
    )


def executor(adapter: ScriptedAndroidAdapter) -> Program3WorkerExecutor:
    return Program3WorkerExecutor(
        scene_engine=SceneEngine(),
        workflow_engine=SceneWorkflowEngine(),
        ui=adapter,
        evidence=adapter,
        checkpoints=adapter,
    )


def test_successful_action_is_verified_before_checkpoint() -> None:
    adapter = ScriptedAndroidAdapter(
        [
            SceneEvidence(texts={"Choose video"}),
            SceneEvidence(texts={"Continue"}),
        ]
    )
    result = executor(adapter).execute_action(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        action_id="SELECT_VIDEO",
    )
    assert result.success
    assert adapter.actions == [("device-1", "SELECT_VIDEO")]
    assert adapter.checkpoints == [("job-1", "VIDEO_PREPARE", "SELECT_VIDEO")]


def test_unknown_current_scene_blocks_action() -> None:
    adapter = ScriptedAndroidAdapter([SceneEvidence(texts={"Unexpected"})])
    result = executor(adapter).execute_action(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        action_id="SELECT_VIDEO",
    )
    assert not result.success
    assert adapter.actions == []
    assert result.recovery is not None
    assert result.recovery.level == "REOBSERVE"


def test_wrong_next_scene_fails_without_checkpoint() -> None:
    adapter = ScriptedAndroidAdapter(
        [
            SceneEvidence(texts={"Choose video"}),
            SceneEvidence(texts={"Publishing"}),
        ]
    )
    result = executor(adapter).execute_action(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        action_id="SELECT_VIDEO",
    )
    assert not result.success
    assert result.reason == "UNEXPECTED_NEXT_SCENE"
    assert adapter.checkpoints == []


def test_destructive_action_with_uncertain_next_scene_requires_human() -> None:
    adapter = ScriptedAndroidAdapter(
        [
            SceneEvidence(texts={"Continue"}),
            SceneEvidence(texts={"Unexpected"}),
        ]
    )
    result = executor(adapter).execute_action(
        publish_job_id="job-1",
        device_id="device-1",
        workflow=workflow(),
        signatures=signatures(),
        action_id="SUBMIT_POST",
        destructive_action=True,
    )
    assert not result.success
    assert result.recovery is not None
    assert result.recovery.level == "NEEDS_HUMAN"
