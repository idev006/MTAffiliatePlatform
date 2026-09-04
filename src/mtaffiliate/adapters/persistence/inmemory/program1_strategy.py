from __future__ import annotations

from threading import RLock

from mtaffiliate.application.program1_strategy import StrategyToWorkResult
from mtaffiliate.ports.repositories.program1_strategy import StrategyWorkConflictError


class InMemoryProgram1StrategyRepository:
    def __init__(self) -> None:
        self._items: dict[str, StrategyToWorkResult] = {}
        self._lock = RLock()

    def put(self, reference: str, package: StrategyToWorkResult) -> None:
        if not reference.strip():
            raise ValueError("strategy work reference must be non-empty")
        with self._lock:
            existing = self._items.get(reference)
            if existing is not None:
                if existing != package:
                    raise StrategyWorkConflictError(
                        f"strategy work reference conflict: {reference}"
                    )
                return
            self._items[reference] = package

    def get(self, reference: str) -> StrategyToWorkResult | None:
        with self._lock:
            return self._items.get(reference)
