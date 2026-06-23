"""Immutable domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Mapping, Optional

SCHEMA_VERSION = 1


class SessionBoundaryKind(str, Enum):
    SESSION_OPEN = "SESSION_OPEN"
    SESSION_END = "SESSION_END"


class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderCommandKind(str, Enum):
    SUBMIT_LIMIT = "SUBMIT_LIMIT"
    SUBMIT_MARKET = "SUBMIT_MARKET"
    CANCEL = "CANCEL"


@dataclass(frozen=True)
class SessionBoundary:
    event_type: ClassVar[str] = "SessionBoundary"
    effective_time: datetime
    kind: SessionBoundaryKind
    symbol: str
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class BarClosed:
    """One closed bar; primary driver for strategy logic."""

    event_type: ClassVar[str] = "BarClosed"
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "synthetic"
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class StrategyIntent:
    """Strategy output; not a broker order until risk approves."""

    event_type: ClassVar[str] = "StrategyIntent"
    signal_id: str
    symbol: str
    direction: TradeDirection
    qty_hint: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class OrderCommand:
    """Risk-approved instruction to execution."""

    event_type: ClassVar[str] = "OrderCommand"
    client_order_id: str
    symbol: str
    side: OrderSide
    kind: OrderCommandKind
    qty: float
    limit_price: Optional[float] = None
    signal_id: str = ""
    schema_version: int = SCHEMA_VERSION
