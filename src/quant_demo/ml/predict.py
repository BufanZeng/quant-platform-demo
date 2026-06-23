"""Load registered models for inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from quant_demo.ml.registry import ModelRegistry


class MLPredictor:
    def __init__(self, registry_dir: str = "models", version: str | None = None):
        self.registry = ModelRegistry(registry_dir)
        self.version = version or self.registry._index.get("latest")
        self.model, self.feature_names, self.metrics = self.registry.load(self.version)

    def should_trade(self, features: dict, threshold: float = 0.5) -> tuple[bool, float]:
        row = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(row)[0, 1])
        else:
            prob = float(self.model.decision_function(row)[0])
            prob = 1 / (1 + np.exp(-prob))
        return prob >= threshold, prob
