"""Pipeline layer boundary tests."""

from datetime import datetime

from quant_demo.engine.features import FeatureRow, Prediction
from quant_demo.engine.trade_constructor import TradeConstructorConfig, build_trade_spec
from quant_demo.strategies.demo_classifier import ThresholdClassifier


def _row(**kwargs) -> FeatureRow:
    defaults = dict(
        bar_close_ts=datetime(2025, 1, 2, 10, 0),
        session_date="2025-01-02",
        symbol="DEMO",
        close=100.0,
        sma_fast=101.0,
        sma_slow=99.0,
        momentum=2.0,
        volatility=1.5,
        signal_active=True,
    )
    defaults.update(kwargs)
    return FeatureRow(**defaults)


def test_prediction_has_no_prices():
    pred = ThresholdClassifier().predict(_row())
    assert pred is not None
    assert pred.direction in ("up", "down")
    assert 0.0 <= pred.confidence <= 1.0
    assert not hasattr(pred, "entry_price")


def test_trade_constructor_adds_structural_prices():
    pred = Prediction(direction="up", confidence=0.8, model_name="test")
    spec = build_trade_spec(_row(), pred, TradeConstructorConfig(sl_pts=2, tp_pts=4))
    assert spec.entry_price == 100.0
    assert spec.sl == 98.0
    assert spec.tp == 104.0
