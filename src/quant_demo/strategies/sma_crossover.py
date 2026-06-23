"""
Placeholder SMA crossover strategy.

This is intentionally generic — it demonstrates the Strategy protocol
without revealing any proprietary signal logic.
"""

from __future__ import annotations

import uuid
from collections import deque

from quant_demo.engine.features import FeatureRow
from quant_demo.events import BarClosed, SessionBoundary, StrategyIntent, TradeDirection
from quant_demo.strategy_protocol import StrategyOutput


class SMACrossoverStrategy:
    name = "sma_crossover"

    def __init__(self, fast: int = 5, slow: int = 20, sl_pts: float = 2.0, tp_pts: float = 4.0):
        self.fast = fast
        self.slow = slow
        self.sl_pts = sl_pts
        self.tp_pts = tp_pts
        self._closes: deque[float] = deque(maxlen=slow)
        self._session_date = ""
        self._feature_log: list[FeatureRow] = []

    def reset_session(self) -> None:
        self._closes.clear()

    def on_session_boundary(self, event: SessionBoundary) -> StrategyOutput:
        self._session_date = event.effective_time.strftime("%Y-%m-%d")
        return StrategyOutput.empty()

    def on_bar(self, bar: BarClosed) -> StrategyOutput:
        self._closes.append(bar.close)
        if len(self._closes) < self.slow:
            return StrategyOutput.empty()

        closes = list(self._closes)
        sma_fast = sum(closes[-self.fast :]) / self.fast
        sma_slow = sum(closes) / self.slow
        prev_fast = sum(closes[-self.fast - 1 : -1]) / self.fast if len(closes) > self.fast else sma_fast
        prev_slow = sum(closes[:-1]) / (self.slow - 1) if len(closes) > 1 else sma_slow

        momentum = bar.close - closes[0]
        volatility = max(closes) - min(closes)
        signal_active = prev_fast <= prev_slow and sma_fast > sma_slow

        session_date = self._session_date or bar.timestamp.strftime("%Y-%m-%d")
        self._feature_log.append(
            FeatureRow(
                bar_close_ts=bar.timestamp,
                session_date=session_date,
                symbol=bar.symbol,
                close=bar.close,
                sma_fast=sma_fast,
                sma_slow=sma_slow,
                momentum=momentum,
                volatility=volatility,
                signal_active=signal_active,
            )
        )

        if not signal_active:
            return StrategyOutput.empty()

        entry = bar.close
        intent = StrategyIntent(
            signal_id=str(uuid.uuid4())[:8],
            symbol=bar.symbol,
            direction=TradeDirection.LONG,
            metadata={
                "entry_price": entry,
                "sl": entry - self.sl_pts,
                "tp": entry + self.tp_pts,
                "strategy": self.name,
            },
        )
        return StrategyOutput(intents=[intent])

    @property
    def feature_log(self) -> list[FeatureRow]:
        return self._feature_log
