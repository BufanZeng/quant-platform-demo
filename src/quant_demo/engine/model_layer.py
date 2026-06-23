"""ModelLayer protocol — plug-in contract for any classifier."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quant_demo.engine.features import FeatureRow, Prediction


@runtime_checkable
class ModelLayer(Protocol):
    name: str

    def predict(self, row: FeatureRow) -> Prediction | None:
        """Pure function of row; None means no signal."""
