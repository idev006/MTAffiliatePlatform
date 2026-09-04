from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.application.program1_strategy import StrategyToWorkResult
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.ports.repositories.program1_strategy import StrategyWorkConflictError

from .models import Program1StrategyWorkRow


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _payload(package: StrategyToWorkResult) -> dict[str, object]:
    return {
        "hypothesis": package.hypothesis.model_dump(mode="json"),
        "signals": [signal.model_dump(mode="json") for signal in package.signals],
        "discovery_plan": package.discovery_plan.model_dump(mode="json"),
    }


def _canonical_json(package: StrategyToWorkResult) -> str:
    return json.dumps(_payload(package), sort_keys=True, separators=(",", ":"))


class SQLAlchemyProgram1StrategyRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def put(self, reference: str, package: StrategyToWorkResult) -> None:
        if not reference.strip():
            raise ValueError("strategy work reference must be non-empty")
        package_json = _canonical_json(package)
        fingerprint = hashlib.sha256(package_json.encode("utf-8")).hexdigest()

        with self._session_factory() as session, session.begin():
            existing = session.get(Program1StrategyWorkRow, reference)
            if existing is not None:
                if existing.fingerprint != fingerprint or existing.package_json != package_json:
                    raise StrategyWorkConflictError(
                        f"strategy work reference conflict: {reference}"
                    )
                return
            session.add(
                Program1StrategyWorkRow(
                    reference=reference,
                    fingerprint=fingerprint,
                    package_json=package_json,
                    created_at=package.discovery_plan.created_at,
                )
            )

    def get(self, reference: str) -> StrategyToWorkResult | None:
        with self._session_factory() as session:
            row = session.get(Program1StrategyWorkRow, reference)
            if row is None:
                return None
            payload = json.loads(row.package_json)

        hypothesis = AffiliateSuccessHypothesis.model_validate(payload["hypothesis"])
        signals = tuple(
            SignalRequirement.model_validate(item) for item in payload["signals"]
        )
        discovery_plan = DiscoveryPlan.model_validate(payload["discovery_plan"])
        # Normalize SQLite's possible naive timestamp only through the validated
        # domain payload if external DB serialization has removed timezone data.
        if discovery_plan.created_at.tzinfo is None:
            discovery_plan = discovery_plan.model_copy(
                update={"created_at": _as_utc(discovery_plan.created_at)}
            )
        return StrategyToWorkResult(
            hypothesis=hypothesis,
            signals=signals,
            discovery_plan=discovery_plan,
        )
