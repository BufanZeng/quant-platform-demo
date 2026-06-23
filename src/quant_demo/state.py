"""Market vs trading state containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from quant_demo.events import BarClosed

__all__ = ["MarketState", "TradingState", "OrderEntry"]


@dataclass(frozen=True)
class MarketState:
    last_bar: Optional[BarClosed] = None
    session_open: bool = False
    session_date: str = ""
    bar_count: int = 0


@dataclass(frozen=True)
class OrderEntry:
    client_order_id: str
    symbol: str
    qty: float
    side: str
    signal_id: str = ""


@dataclass
class TradingState:
    """Authoritative for orders, position, and risk counters."""

    open_orders: List[OrderEntry] = field(default_factory=list)
    position_qty: float = 0.0
    daily_pnl: float = 0.0
    risk_counters: Dict[str, float] = field(default_factory=dict)
    last_update: Optional[datetime] = None
