"""
Strategy interface — boundary between signal logic and execution.

Every strategy implements the ``Strategy`` protocol. Risk, backtest, and live
runners are strategy-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from quant_demo.events import BarClosed, SessionBoundary, StrategyIntent


@dataclass
class StrategyOutput:
    intents: list[StrategyIntent] = field(default_factory=list)

    @staticmethod
    def empty() -> StrategyOutput:
        return StrategyOutput()


@runtime_checkable
class Strategy(Protocol):
    name: str

    def on_bar(self, bar: BarClosed) -> StrategyOutput:
        ...

    def on_session_boundary(self, event: SessionBoundary) -> StrategyOutput:
        ...

    def reset_session(self) -> None:
        ...
