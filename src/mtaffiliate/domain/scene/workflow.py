from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SceneTransition(BaseModel):
    from_scene: str = Field(min_length=1)
    to_scene: str = Field(min_length=1)
    action_id: str = Field(min_length=1)


class SceneWorkflow(BaseModel):
    workflow_id: str = Field(min_length=1)
    start_scene: str = Field(min_length=1)
    terminal_scenes: set[str] = Field(min_length=1)
    transitions: list[SceneTransition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self) -> SceneWorkflow:
        scenes = {self.start_scene, *self.terminal_scenes}
        for transition in self.transitions:
            scenes.add(transition.from_scene)
            scenes.add(transition.to_scene)
        if not self.terminal_scenes.issubset(scenes):
            raise ValueError("terminal scenes must belong to workflow")
        return self


class TransitionDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1)
    expected_scene: str | None = None


class RecoveryDecision(BaseModel):
    level: Literal["REOBSERVE", "LOCAL", "SAFE_ANCHOR", "RESTART", "NEEDS_HUMAN"]
    reason: str = Field(min_length=1)
