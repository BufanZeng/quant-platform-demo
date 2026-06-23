"""Versioned model storage."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


class ModelRegistry:
    def __init__(self, base_dir: str = "models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "registry.json"
        self._index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {"versions": [], "latest": None}

    def _save_index(self) -> None:
        self.index_path.write_text(json.dumps(self._index, indent=2, default=str))

    def _next_version(self) -> str:
        if not self._index["versions"]:
            return "v001"
        nums = [int(v.lstrip("v")) for v in self._index["versions"]]
        return f"v{max(nums) + 1:03d}"

    def register(
        self,
        model: Any,
        config,
        metrics: dict,
        feature_names: list[str],
        notes: str = "",
    ) -> str:
        version = self._next_version()
        version_dir = self.base_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        with open(version_dir / "model.pkl", "wb") as f:
            pickle.dump(model, f)

        (version_dir / "config.json").write_text(config.to_json())
        (version_dir / "features.json").write_text(json.dumps(feature_names, indent=2))
        (version_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
        (version_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "version": version,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "algorithm": config.model.algorithm,
                    "target": config.dataset.target_column,
                    "notes": notes,
                },
                indent=2,
            )
        )

        self._index["versions"].append(version)
        self._index["latest"] = version
        self._save_index()
        return version

    def load(self, version: str | None = None) -> tuple[Any, list[str], dict]:
        version = version or self._index.get("latest")
        if not version:
            raise FileNotFoundError("No models registered")
        version_dir = self.base_dir / version
        with open(version_dir / "model.pkl", "rb") as f:
            model = pickle.load(f)
        features = json.loads((version_dir / "features.json").read_text())
        metrics = json.loads((version_dir / "metrics.json").read_text())
        return model, features, metrics
