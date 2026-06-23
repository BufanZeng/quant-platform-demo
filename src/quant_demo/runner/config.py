"""Runner configuration — single object wires all modular components."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quant_demo.risk import RiskConfig


@dataclass
class RunnerConfig:
    """Shell config: feed path, risk limits, and component toggles."""

    data_path: Path
    symbol: str = "DEMO"
    strategy_name: str = "sma_crossover"
    risk: RiskConfig = field(default_factory=RiskConfig)
    use_ml_pipeline: bool = False
    flatten_on_session_end: bool = True
    reconcile_sl_window: int = 10
    reconcile_sl_threshold: float = 0.75
    point_value: float = 1.0
