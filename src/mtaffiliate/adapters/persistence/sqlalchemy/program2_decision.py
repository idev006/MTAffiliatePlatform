from __future__ import annotations

import hashlib
import json
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.affiliate_offer.models import OfferSelectionDecision
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionConflictError

from .models import Program2SelectionDecisionRow


class SQLAlchemyProgram2DecisionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fingerprint(decision: OfferSelectionDecision) -> str:
        return hashlib.sha256(decision.model_dump_json().encode("utf-8")).hexdigest()

    @staticmethod
    def _row(decision: OfferSelectionDecision) -> Program2SelectionDecisionRow:
        return Program2SelectionDecisionRow(
            decision_id=decision.decision_id,
            product_id=decision.product_id,
            affiliate_account_id=decision.affiliate_account_id,
            source_job_id=decision.source_job_id,
            selected_at=decision.selected_at,
            preferred_offer_id=decision.preferred_offer_id,
            backup_offer_ids=json.dumps(decision.backup_offer_ids),
            preferred_commercial_key=json.dumps(decision.preferred_commercial_key),
            evidence_refs=json.dumps(decision.evidence_refs),
            feature_policy_version=decision.feature_policy_version,
            qualification_policy_version=decision.qualification_policy_version,
            decision_policy_version=decision.decision_policy_version,
            reasons=json.dumps(decision.reasons),
            risks=json.dumps(decision.risks),
            fingerprint=SQLAlchemyProgram2DecisionRepository._fingerprint(decision),
        )

    @staticmethod
    def _domain(row: Program2SelectionDecisionRow) -> OfferSelectionDecision:
        selected_at = row.selected_at
        if selected_at.tzinfo is None:
            selected_at = selected_at.replace(tzinfo=UTC)
        return OfferSelectionDecision(
            decision_id=row.decision_id,
            product_id=row.product_id,
            affiliate_account_id=row.affiliate_account_id,
            source_job_id=row.source_job_id,
            selected_at=selected_at,
            preferred_offer_id=row.preferred_offer_id,
            backup_offer_ids=tuple(json.loads(row.backup_offer_ids)),
            preferred_commercial_key=tuple(json.loads(row.preferred_commercial_key)),
            evidence_refs=tuple(json.loads(row.evidence_refs)),
            feature_policy_version=row.feature_policy_version,
            qualification_policy_version=row.qualification_policy_version,
            decision_policy_version=row.decision_policy_version,
            reasons=tuple(json.loads(row.reasons)),
            risks=tuple(json.loads(row.risks)),
        )

    def put(self, decision: OfferSelectionDecision) -> None:
        fingerprint = self._fingerprint(decision)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program2SelectionDecisionRow, decision.decision_id)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program2DecisionConflictError(
                        f"Program 2 decision conflict: {decision.decision_id}"
                    )
                return
            session.add(self._row(decision))

    def get(self, decision_id: str) -> OfferSelectionDecision | None:
        with self._session_factory() as session:
            row = session.get(Program2SelectionDecisionRow, decision_id)
            return None if row is None else self._domain(row)

    def latest_for_product_account(
        self,
        product_id: str,
        affiliate_account_id: str,
    ) -> OfferSelectionDecision | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(Program2SelectionDecisionRow)
                .where(
                    Program2SelectionDecisionRow.product_id == product_id,
                    Program2SelectionDecisionRow.affiliate_account_id
                    == affiliate_account_id,
                )
                .order_by(
                    Program2SelectionDecisionRow.selected_at.desc(),
                    Program2SelectionDecisionRow.decision_id.desc(),
                )
            )
        return None if row is None else self._domain(row)
