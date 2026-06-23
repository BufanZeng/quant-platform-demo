"""Typed layer boundaries for the ML pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal


@dataclass
class FeatureRow:
    """Flat feature vector at bar close — training record for offline ML."""

    bar_close_ts: datetime
    session_date: str
    symbol: str
    close: float
    sma_fast: float
    sma_slow: float
    momentum: float
    volatility: float
    signal_active: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bar_close_ts"] = self.bar_close_ts.isoformat()
        return d


@dataclass
class Prediction:
    """Model output: direction + confidence only (no prices)."""

    direction: Literal["up", "down"]
    confidence: float
    model_name: str


@dataclass
class TradeSpec:
    """Complete trade description for the risk gate."""

    symbol: str
    session_date: str
    bar_close_ts: datetime
    side: Literal["up", "down"]
    entry_price: float
    sl: float
    tp: float
    contracts: int
    confidence: float
    model_name: str
