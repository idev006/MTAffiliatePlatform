from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.program2_artifact import (
    InMemoryProgram2ArtifactRepository,
)
from mtaffiliate.adapters.persistence.inmemory.program2_decision import (
    InMemoryProgram2DecisionRepository,
)
from mtaffiliate.application.program2_artifacts import (
    Program2ArtifactService,
    Program2HandoffPolicy,
)
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
    OfferSelectionDecision,
)

NOW = datetime(2026, 9, 4, 17, 0, tzinfo=UTC)


def decision() -> OfferSelectionDecision:
    return OfferSelectionDecision(
        decision_id="p2d-1",
        product_id="shopee:shop-1:item-1",
        affiliate_account_id="account-1",
        source_job_id="job-1",
        selected_at=NOW,
        preferred_offer_id="offer-1",
        backup_offer_ids=("offer-2",),
        preferred_commercial_key=(
            "shopee",
            "shop-1",
            "item-1",
            "offer-1",
            "account-1",
        ),
        evidence_refs=("offer-obs-1",),
        feature_policy_version="features-v1",
        qualification_policy_version="qualification-v1",
        decision_policy_version="selection-v1",
        reasons=("controlled selection",),
    )


def artifact(**overrides) -> AffiliateLinkArtifact:
    values = {
        "artifact_id": "artifact-1",
        "selection_decision_id": "p2d-1",
        "source_job_id": "job-1",
        "affiliate_account_id": "account-1",
        "offer_id": "offer-1",
        "link_url": "https://example.invalid/affiliate/abc",
        "created_at": NOW + timedelta(minutes=1),
        "validated_at": NOW + timedelta(minutes=2),
        "validation_state": LinkArtifactValidationState.LAB_VALIDATED,
        "evidence_refs": ("export-evidence-1",),
    }
    values.update(overrides)
    return AffiliateLinkArtifact(**values)


def build(policy: Program2HandoffPolicy | None = None):
    decisions = InMemoryProgram2DecisionRepository()
    artifacts = InMemoryProgram2ArtifactRepository()
    decisions.put(decision())
    return decisions, artifacts, Program2ArtifactService(
        decisions=decisions,
        artifacts=artifacts,
        policy=policy,
    )


def test_validated_artifact_builds_traceable_program3_handoff() -> None:
    decisions, artifacts, service = build()
    registered = service.register_artifact(artifact())

    handoff = service.build_program3_handoff(
        "p2d-1",
        as_of=NOW + timedelta(minutes=3),
    )

    assert artifacts.get("artifact-1") == registered
    assert decisions.get("p2d-1") is not None
    assert handoff.selection_decision_id == "p2d-1"
    assert handoff.preferred_offer_id == "offer-1"
    assert handoff.backup_offer_ids == ("offer-2",)
    assert handoff.link_artifact_id == "artifact-1"
    assert set(handoff.evidence_refs) == {"offer-obs-1", "export-evidence-1"}


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"source_job_id": "wrong"}, "source_job_id"),
        ({"affiliate_account_id": "wrong"}, "affiliate account"),
        ({"offer_id": "wrong"}, "preferred selection"),
        ({"link_url": "not-a-url"}, "valid web URL"),
    ],
)
def test_artifact_identity_and_url_mismatch_fail_closed(
    override: dict[str, object],
    message: str,
) -> None:
    _decisions, _artifacts, service = build()
    with pytest.raises(ValueError, match=message):
        service.register_artifact(artifact(**override))


def test_validated_at_cannot_precede_creation() -> None:
    _decisions, _artifacts, service = build()
    with pytest.raises(ValueError, match="validated_at"):
        service.register_artifact(
            artifact(
                created_at=NOW + timedelta(minutes=2),
                validated_at=NOW + timedelta(minutes=1),
            )
        )


def test_unknown_selection_cannot_accept_artifact() -> None:
    _decisions, _artifacts, service = build()
    with pytest.raises(ValueError, match="selection decision does not exist"):
        service.register_artifact(
            artifact(selection_decision_id="missing")
        )


def test_stale_selection_blocks_program3_handoff() -> None:
    _decisions, _artifacts, service = build(
        Program2HandoffPolicy(max_selection_age=timedelta(minutes=5))
    )
    service.register_artifact(artifact())

    with pytest.raises(ValueError, match="stale"):
        service.build_program3_handoff(
            "p2d-1",
            as_of=NOW + timedelta(minutes=10),
        )


def test_unready_or_unvalidated_artifact_blocks_handoff() -> None:
    _decisions, _artifacts, service = build()
    service.register_artifact(
        artifact(
            validation_state=LinkArtifactValidationState.OUTCOME_UNKNOWN,
            validated_at=None,
        )
    )
    with pytest.raises(ValueError, match="not handoff-ready"):
        service.build_program3_handoff(
            "p2d-1",
            as_of=NOW + timedelta(minutes=3),
        )


def test_handoff_requires_artifact_and_known_selection() -> None:
    _decisions, _artifacts, service = build()
    with pytest.raises(ValueError, match="validated affiliate link artifact"):
        service.build_program3_handoff(
            "p2d-1",
            as_of=NOW + timedelta(minutes=1),
        )
    with pytest.raises(ValueError, match="selection decision does not exist"):
        service.build_program3_handoff(
            "missing",
            as_of=NOW + timedelta(minutes=1),
        )


def test_handoff_as_of_cannot_precede_selection() -> None:
    _decisions, _artifacts, service = build()
    with pytest.raises(ValueError, match="cannot precede selection"):
        service.build_program3_handoff(
            "p2d-1",
            as_of=NOW - timedelta(seconds=1),
        )


def test_handoff_policy_validates_configuration() -> None:
    with pytest.raises(ValueError):
        Program2HandoffPolicy(version=" ")
    with pytest.raises(ValueError):
        Program2HandoffPolicy(max_selection_age=timedelta(0))
    with pytest.raises(ValueError):
        Program2HandoffPolicy(allowed_validation_states=())
