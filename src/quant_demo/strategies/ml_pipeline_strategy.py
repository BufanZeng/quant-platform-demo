"""
Full ML pipeline strategy — demonstrates modular layer boundaries.

FeatureRow → ModelLayer → Prediction → TradeConstructor → StrategyIntent

Signal logic is a placeholder (SMA crossover features + threshold classifier).
"""

from __future__ import annotations

import uuid
from collections import deque

from quant_demo.engine.features import FeatureRow
from quant_demo.engine.trade_constructor import TradeConstructorConfig, build_trade_spec
from quant_demo.events import BarClosed, SessionBoundary, StrategyIntent, TradeDirection
from quant_demo.strategies.demo_classifier import ThresholdClassifier
from quant_demo.strategy_protocol import StrategyOutput


class MLPipelineStrategy:
    name = "ml_pipeline"

    def __init__(self) -> None:
        self._closes: deque[float] = deque(maxlen=20)
        self._model = ThresholdClassifier()
        self._trade_cfg = TradeConstructorConfig(sl_pts=2.0, tp_pts=4.0)
        self._feature_log: list[FeatureRow] = []

    def reset_session(self) -> None:
        self._closes.clear()

    def on_session_boundary(self, event: SessionBoundary) -> StrategyOutput:
        return StrategyOutput.empty()

    def on_bar(self, bar: BarClosed) -> StrategyOutput:
        self._closes.append(bar.close)
        if len(self._closes) < 20:
            return StrategyOutput.empty()

        closes = list(self._closes)
        sma_fast = sum(closes[-5:]) / 5
        sma_slow = sum(closes) / 20
        row = FeatureRow(
            bar_close_ts=bar.timestamp,
            session_date=bar.timestamp.strftime("%Y-%m-%d"),
            symbol=bar.symbol,
            close=bar.close,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
            momentum=bar.close - closes[0],
            volatility=max(closes) - min(closes),
            signal_active=sma_fast > sma_slow,
        )
        self._feature_log.append(row)

        prediction = self._model.predict(row)
        if prediction is None:
            return StrategyOutput.empty()

        spec = build_trade_spec(row, prediction, self._trade_cfg)
        direction = TradeDirection.LONG if spec.side == "up" else TradeDirection.SHORT
        intent = StrategyIntent(
            signal_id=str(uuid.uuid4())[:8],
            symbol=bar.symbol,
            direction=direction,
            metadata={
                "entry_price": spec.entry_price,
                "sl": spec.sl,
                "tp": spec.tp,
                "confidence": spec.confidence,
                "model_name": spec.model_name,
            },
        )
        return StrategyOutput(intents=[intent])

    @property
    def feature_log(self) -> list[FeatureRow]:
        return self._feature_log
