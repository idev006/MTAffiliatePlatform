from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.scene.models import SceneEvidence


class DeviceTransportPort(Protocol):
    def is_connected(self, device_id: str) -> bool: ...

    def restart_app(self, device_id: str, package_name: str) -> None: ...


class UIAutomationPort(Protocol):
    def perform_action(self, device_id: str, action_id: str) -> None: ...


class SceneEvidencePort(Protocol):
    def capture(self, device_id: str) -> SceneEvidence: ...


class CheckpointPort(Protocol):
    def save_checkpoint(
        self,
        publish_job_id: str,
        scene_id: str,
        action_id: str,
    ) -> None: ...
