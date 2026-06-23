"""Load parquet and apply temporal train/val/test splits."""

from __future__ import annotations

import pandas as pd

from quant_demo.ml.config import PipelineConfig


def load_dataset(config: PipelineConfig) -> pd.DataFrame:
    df = pd.read_parquet(config.dataset.parquet_path)
    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    if not feature_cols:
        raise ValueError("No feature_* columns found")
    return df.dropna(subset=[config.dataset.target_column])


def temporal_split(df: pd.DataFrame, config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.to_datetime(df["audit_date"])
    train = df[dates <= config.dataset.train_end]
    val = df[(dates > config.dataset.train_end) & (dates <= config.dataset.val_end)]
    test = df[dates > config.dataset.val_end]
    return train, val, test


def feature_columns(df: pd.DataFrame, max_features: int) -> list[str]:
    cols = [c for c in df.columns if c.startswith("feature_")]
    if len(cols) <= max_features:
        return cols
    target_cols = [c for c in df.columns if c.startswith("target_")]
    if not target_cols:
        return cols[:max_features]
    corr = df[cols].corrwith(df[target_cols[0]]).abs()
    return corr.sort_values(ascending=False).head(max_features).index.tolist()
