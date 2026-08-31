from __future__ import annotations

from collections import deque

from mtaffiliate.domain.scene.models import SceneEvidence


class ScriptedAndroidAdapter:
    """Deterministic Device/UI/Scene fake for Program 3 workflow tests."""

    def __init__(
        self,
        evidence_script: list[SceneEvidence],
        *,
        connected: bool = True,
    ) -> None:
        self._evidence = deque(evidence_script)
        self.connected = connected
        self.actions: list[tuple[str, str]] = []
        self.restarts: list[tuple[str, str]] = []
        self.checkpoints: list[tuple[str, str, str]] = []

    def is_connected(self, _device_id: str) -> bool:
        return self.connected

    def restart_app(self, device_id: str, package_name: str) -> None:
        if not self.connected:
            raise ConnectionError("device disconnected")
        self.restarts.append((device_id, package_name))

    def perform_action(self, device_id: str, action_id: str) -> None:
        if not self.connected:
            raise ConnectionError("device disconnected")
        self.actions.append((device_id, action_id))

    def capture(self, _device_id: str) -> SceneEvidence:
        if not self.connected:
            raise ConnectionError("device disconnected")
        if not self._evidence:
            raise RuntimeError("scripted scene evidence exhausted")
        return self._evidence.popleft()

    def save_checkpoint(
        self,
        publish_job_id: str,
        scene_id: str,
        action_id: str,
    ) -> None:
        self.checkpoints.append((publish_job_id, scene_id, action_id))
