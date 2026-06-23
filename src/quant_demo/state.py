"""Market vs trading state containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from quant_demo.events import BarClosed
from quant_demo.lifecycle import OrderRole, PositionGroupStatus

__all__ = [
    "MarketState",
    "TradingState",
    "OrderEntry",
    "PositionGroup",
    "reduce_market_state",
]


@dataclass(frozen=True)
class MarketState:
    """
    Rolling market view from the feed. Strategy reads; never mutates broker state.
    """

    last_bar: Optional[BarClosed] = None
    session_open: bool = False
    session_date: str = ""
    bar_count: int = 0


def reduce_market_state(market: MarketState, bar: BarClosed) -> MarketState:
    session_date = market.session_date or bar.timestamp.strftime("%Y-%m-%d")
    return MarketState(
        last_bar=bar,
        session_open=True,
        session_date=session_date,
        bar_count=market.bar_count + 1,
    )


@dataclass(frozen=True)
class OrderEntry:
    """Snapshot of one working order leg in a bracket group."""

    client_order_id: str
    symbol: str
    qty: float
    side: str
    signal_id: str = ""
    position_group_id: str = ""
    order_role: OrderRole = OrderRole.ENTRY


@dataclass
class PositionGroup:
    """
    Tracks all three legs of a single bracket trade.

    See ``quant_demo.lifecycle`` for the state machine diagram and valid transitions.
    """

    group_id: str
    signal_id: str
    symbol: str
    qty: float = 1.0
    status: PositionGroupStatus = PositionGroupStatus.ENTRY_PENDING
    outcome: str = ""  # "TP" | "SL" | "CANCEL" | "TIMEOUT" | ""
    entry_client_order_id: str = ""
    tp_client_order_id: str = ""
    sl_client_order_id: str = ""
    entry_price: float = 0.0
    tp_price: float = 0.0
    sl_price: float = 0.0
    oca_group: str = ""


@dataclass
class TradingState:
    """Authoritative for orders, bracket groups, position, and risk counters."""

    open_orders: Dict[str, OrderEntry] = field(default_factory=dict)
    position_groups: Dict[str, PositionGroup] = field(default_factory=dict)
    position_qty: float = 0.0
    daily_pnl: float = 0.0
    risk_counters: Dict[str, float] = field(default_factory=dict)
    reconcile_outcomes: List[str] = field(default_factory=list)
    last_update: Optional[datetime] = None
