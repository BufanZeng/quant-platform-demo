"""Immutable domain events — the spine shared by backtest and live adapters."""

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
    SUBMIT_STOP = "SUBMIT_STOP"
    CANCEL = "CANCEL"
    CANCEL_ALL = "CANCEL_ALL"


class OrderStatusReason(str, Enum):
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    OTHER = "OTHER"


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
    stop_price: Optional[float] = None
    signal_id: str = ""
    position_group_id: str = ""
    oca_group: str = ""
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class FillLeg:
    """One execution fill; idempotent on fill_id."""

    event_type: ClassVar[str] = "FillLeg"
    fill_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    qty: float
    price: float
    timestamp: datetime
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class OrderDone:
    """Terminal order state from broker / simulated adapter."""

    event_type: ClassVar[str] = "OrderDone"
    client_order_id: str
    symbol: str
    reason: OrderStatusReason
    timestamp: datetime
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class AccountSnapshot:
    """Broker-wins reconciliation snapshot."""

    event_type: ClassVar[str] = "AccountSnapshot"
    symbol: str
    position_qty: float
    timestamp: datetime
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class AttemptLifecycleUpdate:
    """Runner → strategy bookkeeping after broker events."""

    event_type: ClassVar[str] = "AttemptLifecycleUpdate"
    position_group_id: str
    phase: str  # "entry_filled" | "terminal"
    observed_at: datetime
    schema_version: int = SCHEMA_VERSION
