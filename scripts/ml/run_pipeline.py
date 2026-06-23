#!/usr/bin/env python3
"""Train and register a demo ML model from config JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quant_demo.ml.config import PipelineConfig
from quant_demo.ml.data_prep import feature_columns, load_dataset, temporal_split
from quant_demo.ml.registry import ModelRegistry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "ml_demo.json")
    parser.add_argument("--notes", default="demo run")
    args = parser.parse_args()

    config = PipelineConfig.from_json(args.config)
    df = load_dataset(config)
    train, val, test = temporal_split(df, config)
    features = feature_columns(train, config.model.max_features)
    target = config.dataset.target_column

    model = LogisticRegression(class_weight=config.model.class_weight, max_iter=500)
    model.fit(train[features], train[target])

    def _metrics(split, name: str) -> dict:
        if split.empty:
            return {f"{name}_auc": None, f"{name}_accuracy": None}
        prob = model.predict_proba(split[features])[:, 1]
        pred = (prob >= 0.5).astype(int)
        return {
            f"{name}_auc": float(roc_auc_score(split[target], prob)),
            f"{name}_accuracy": float(accuracy_score(split[target], pred)),
        }

    metrics = {}
    metrics.update(_metrics(train, "train"))
    metrics.update(_metrics(val, "val"))
    metrics.update(_metrics(test, "test"))

    registry = ModelRegistry(str(ROOT / "models"))
    version = registry.register(model, config, metrics, features, notes=args.notes)

    print(f"Registered {version}")
    for k, v in metrics.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
