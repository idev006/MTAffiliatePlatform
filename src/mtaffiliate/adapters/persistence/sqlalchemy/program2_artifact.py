from __future__ import annotations

import hashlib
import json
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    LinkArtifactValidationState,
)
from mtaffiliate.ports.repositories.program2_artifact import Program2ArtifactConflictError

from .models import Program2LinkArtifactRow


class SQLAlchemyProgram2ArtifactRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fingerprint(artifact: AffiliateLinkArtifact) -> str:
        return hashlib.sha256(artifact.model_dump_json().encode("utf-8")).hexdigest()

    @staticmethod
    def _row(artifact: AffiliateLinkArtifact) -> Program2LinkArtifactRow:
        return Program2LinkArtifactRow(
            artifact_id=artifact.artifact_id,
            selection_decision_id=artifact.selection_decision_id,
            source_job_id=artifact.source_job_id,
            affiliate_account_id=artifact.affiliate_account_id,
            offer_id=artifact.offer_id,
            link_url=artifact.link_url,
            created_at=artifact.created_at,
            validated_at=artifact.validated_at,
            validation_state=artifact.validation_state.value,
            evidence_refs=json.dumps(artifact.evidence_refs),
            fingerprint=SQLAlchemyProgram2ArtifactRepository._fingerprint(artifact),
        )

    @staticmethod
    def _domain(row: Program2LinkArtifactRow) -> AffiliateLinkArtifact:
        created_at = row.created_at
        validated_at = row.validated_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if validated_at is not None and validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=UTC)
        return AffiliateLinkArtifact(
            artifact_id=row.artifact_id,
            selection_decision_id=row.selection_decision_id,
            source_job_id=row.source_job_id,
            affiliate_account_id=row.affiliate_account_id,
            offer_id=row.offer_id,
            link_url=row.link_url,
            created_at=created_at,
            validated_at=validated_at,
            validation_state=LinkArtifactValidationState(row.validation_state),
            evidence_refs=tuple(json.loads(row.evidence_refs)),
        )

    def put(self, artifact: AffiliateLinkArtifact) -> None:
        fingerprint = self._fingerprint(artifact)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program2LinkArtifactRow, artifact.artifact_id)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program2ArtifactConflictError(
                        f"Program 2 artifact conflict: {artifact.artifact_id}"
                    )
                return
            session.add(self._row(artifact))

    def get(self, artifact_id: str) -> AffiliateLinkArtifact | None:
        with self._session_factory() as session:
            row = session.get(Program2LinkArtifactRow, artifact_id)
            return None if row is None else self._domain(row)

    def latest_for_selection(self, selection_decision_id: str) -> AffiliateLinkArtifact | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(Program2LinkArtifactRow)
                .where(
                    Program2LinkArtifactRow.selection_decision_id
                    == selection_decision_id
                )
                .order_by(
                    Program2LinkArtifactRow.validated_at.desc().nullslast(),
                    Program2LinkArtifactRow.created_at.desc(),
                    Program2LinkArtifactRow.artifact_id.desc(),
                )
            )
        return None if row is None else self._domain(row)
