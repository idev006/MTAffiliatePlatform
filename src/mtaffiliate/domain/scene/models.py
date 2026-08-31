from __future__ import annotations

from pydantic import BaseModel, Field


class SceneEvidence(BaseModel):
    package_name: str | None = None
    activity_name: str | None = None
    resource_ids: set[str] = Field(default_factory=set)
    texts: set[str] = Field(default_factory=set)
    content_descriptions: set[str] = Field(default_factory=set)


class SceneSignature(BaseModel):
    scene_id: str = Field(min_length=1)
    required_resource_ids: set[str] = Field(default_factory=set)
    required_texts: set[str] = Field(default_factory=set)
    negative_resource_ids: set[str] = Field(default_factory=set)
    negative_texts: set[str] = Field(default_factory=set)
    expected_package: str | None = None


class SceneRecognition(BaseModel):
    scene_id: str | None = None
    status: str = Field(pattern="^(CONFIRMED|UNKNOWN|AMBIGUOUS)$")
    matched_signatures: list[str] = Field(default_factory=list)
