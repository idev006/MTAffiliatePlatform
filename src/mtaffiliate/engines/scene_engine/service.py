from __future__ import annotations

from mtaffiliate.domain.scene.models import (
    SceneEvidence,
    SceneRecognition,
    SceneSignature,
)


class SceneEngine:
    """Deterministic scene recognizer for fixture/device evidence.

    Real Shopee signatures remain configuration/fixture driven and are not
    hard-coded here.
    """

    def recognize(
        self,
        evidence: SceneEvidence,
        signatures: list[SceneSignature],
    ) -> SceneRecognition:
        matches = [signature.scene_id for signature in signatures if self._matches(evidence, signature)]
        if not matches:
            return SceneRecognition(status="UNKNOWN")
        if len(matches) > 1:
            return SceneRecognition(status="AMBIGUOUS", matched_signatures=matches)
        return SceneRecognition(
            scene_id=matches[0],
            status="CONFIRMED",
            matched_signatures=matches,
        )

    @staticmethod
    def _matches(evidence: SceneEvidence, signature: SceneSignature) -> bool:
        if signature.expected_package and signature.expected_package != evidence.package_name:
            return False
        if not signature.required_resource_ids.issubset(evidence.resource_ids):
            return False
        if not signature.required_texts.issubset(evidence.texts):
            return False
        if signature.negative_resource_ids.intersection(evidence.resource_ids):
            return False
        return not signature.negative_texts.intersection(evidence.texts)
