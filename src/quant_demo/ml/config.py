"""Pipeline configuration dataclasses."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class DatasetConfig:
    parquet_path: str
    target_column: str
    train_end: str
    val_end: str


@dataclass
class ModelConfig:
    algorithm: str = "logistic_regression"
    max_features: int = 4
    class_weight: str = "balanced"


@dataclass
class PipelineConfig:
    description: str
    dataset: DatasetConfig
    model: ModelConfig

    @classmethod
    def from_json(cls, path: Path) -> PipelineConfig:
        raw = json.loads(path.read_text())
        return cls(
            description=raw["description"],
            dataset=DatasetConfig(**raw["dataset"]),
            model=ModelConfig(**raw.get("model", {})),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
