"""Demo rule-based model implementing ModelLayer."""

from __future__ import annotations

from quant_demo.engine.features import FeatureRow, Prediction
from quant_demo.engine.model_layer import ModelLayer


class ThresholdClassifier:
    """Rule-based stand-in for a trained classifier."""

    name = "threshold_demo"

    def __init__(self, min_momentum: float = 0.0):
        self.min_momentum = min_momentum

    def predict(self, row: FeatureRow) -> Prediction | None:
        if not row.signal_active:
            return None
        if row.momentum < self.min_momentum:
            return None
        confidence = min(1.0, abs(row.momentum) / max(row.volatility, 1e-6))
        direction = "up" if row.sma_fast >= row.sma_slow else "down"
        return Prediction(direction=direction, confidence=confidence, model_name=self.name)
