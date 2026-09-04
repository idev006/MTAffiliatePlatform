from __future__ import annotations

from typing import Protocol

from mtaffiliate.application.program1_strategy import StrategyToWorkResult


class StrategyWorkConflictError(RuntimeError):
    pass


class Program1StrategyRepository(Protocol):
    def put(self, reference: str, package: StrategyToWorkResult) -> None: ...

    def get(self, reference: str) -> StrategyToWorkResult | None: ...
