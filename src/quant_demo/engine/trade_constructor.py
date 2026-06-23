"""Prediction + context → TradeSpec (structural SL/TP, not from the model)."""

from __future__ import annotations

from dataclasses import dataclass

from quant_demo.engine.features import FeatureRow, Prediction, TradeSpec


@dataclass(frozen=True)
class TradeConstructorConfig:
    sl_pts: float = 2.0
    tp_pts: float = 4.0
    contracts: int = 1


def build_trade_spec(
    row: FeatureRow,
    prediction: Prediction,
    config: TradeConstructorConfig | None = None,
) -> TradeSpec:
    cfg = config or TradeConstructorConfig()
    entry = row.close
    if prediction.direction == "up":
        sl = entry - cfg.sl_pts
        tp = entry + cfg.tp_pts
    else:
        sl = entry + cfg.sl_pts
        tp = entry - cfg.tp_pts

    return TradeSpec(
        symbol=row.symbol,
        session_date=row.session_date,
        bar_close_ts=row.bar_close_ts,
        side=prediction.direction,
        entry_price=entry,
        sl=sl,
        tp=tp,
        contracts=cfg.contracts,
        confidence=prediction.confidence,
        model_name=prediction.model_name,
    )
