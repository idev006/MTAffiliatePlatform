from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.program1.opportunity import OpportunityDecisionRecord
from mtaffiliate.ports.repositories.program1_opportunity import (
    OpportunityDecisionConflictError,
)

from .models import Program1OpportunityDecisionRow


class SQLAlchemyProgram1OpportunityRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fingerprint(decision: OpportunityDecisionRecord) -> str:
        return hashlib.sha256(decision.model_dump_json().encode("utf-8")).hexdigest()

    @staticmethod
    def _row(decision: OpportunityDecisionRecord) -> Program1OpportunityDecisionRow:
        platform, shop_id, item_id = decision.thesis.product_key
        return Program1OpportunityDecisionRow(
            decision_id=decision.decision_id,
            campaign_id=decision.campaign_id,
            hypothesis_id=decision.hypothesis_id,
            source_job_id=decision.source_job_id,
            platform=platform,
            shop_id=shop_id,
            item_id=item_id,
            evaluated_at=decision.evaluated_at,
            recommended_action=decision.thesis.recommended_action.value,
            feature_policy_version=decision.thesis.feature_policy_version,
            qualification_policy_version=decision.thesis.qualification_policy_version,
            evidence_state=decision.thesis.evidence_state.value,
            fingerprint=SQLAlchemyProgram1OpportunityRepository._fingerprint(decision),
            thesis_json=decision.model_dump_json(),
        )

    @staticmethod
    def _domain(row: Program1OpportunityDecisionRow) -> OpportunityDecisionRecord:
        return OpportunityDecisionRecord.model_validate_json(row.thesis_json)

    def put(self, decision: OpportunityDecisionRecord) -> None:
        fingerprint = self._fingerprint(decision)
        try:
            with self._session_factory() as session, session.begin():
                existing = session.get(Program1OpportunityDecisionRow, decision.decision_id)
                if existing is not None:
                    if existing.fingerprint != fingerprint:
                        raise OpportunityDecisionConflictError(
                            f"opportunity decision conflict: {decision.decision_id}"
                        )
                    return
                session.add(self._row(decision))
                session.flush()
        except IntegrityError as exc:
            raise OpportunityDecisionConflictError(
                f"opportunity decision conflict: {decision.decision_id}"
            ) from exc

    def get(self, decision_id: str) -> OpportunityDecisionRecord | None:
        with self._session_factory() as session:
            row = session.get(Program1OpportunityDecisionRow, decision_id)
            return None if row is None else self._domain(row)

    def latest_for_product(
        self,
        product_key: tuple[str, str, str],
    ) -> OpportunityDecisionRecord | None:
        platform, shop_id, item_id = product_key
        with self._session_factory() as session:
            row = session.scalar(
                select(Program1OpportunityDecisionRow)
                .where(
                    Program1OpportunityDecisionRow.platform == platform,
                    Program1OpportunityDecisionRow.shop_id == shop_id,
                    Program1OpportunityDecisionRow.item_id == item_id,
                )
                .order_by(
                    Program1OpportunityDecisionRow.evaluated_at.desc(),
                    Program1OpportunityDecisionRow.decision_id.desc(),
                )
            )
        return None if row is None else self._domain(row)

    def list_for_campaign(self, campaign_id: str) -> list[OpportunityDecisionRecord]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(Program1OpportunityDecisionRow)
                .where(Program1OpportunityDecisionRow.campaign_id == campaign_id)
                .order_by(
                    Program1OpportunityDecisionRow.evaluated_at.desc(),
                    Program1OpportunityDecisionRow.decision_id.desc(),
                )
            ).all()
        return [self._domain(row) for row in rows]
