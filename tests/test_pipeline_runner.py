"""End-to-end pipeline runner smoke test."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from quant_demo.engine.bar_feed import BarFeed
from quant_demo.runner.config import RunnerConfig
from quant_demo.runner.pipeline_runner import run_pipeline
from quant_demo.strategies.sma_crossover import SMACrossoverStrategy


def _bars(n: int = 100) -> pd.DataFrame:
    rows = []
    price = 100.0
    for i in range(n):
        price += 0.2 if i % 8 < 5 else -0.1
        rows.append(
            {
                "symbol": "DEMO",
                "timeframe": "5m",
                "timestamp": datetime(2025, 1, 2, 9, 30) + pd.Timedelta(minutes=5 * i),
                "open": price,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": 100,
                "source": "test",
            }
        )
    return pd.DataFrame(rows)


def test_pipeline_runner_smoke():
    cfg = RunnerConfig(
        data_path=Path("data/synthetic/demo_bars.parquet"),
        reconcile_sl_threshold=1.0,  # disable SL-ratio alerts in unit test
    )
    result = run_pipeline(SMACrossoverStrategy(fast=3, slow=10), BarFeed(_bars(150)), cfg)
    assert result.strategy_name == "sma_crossover"
    assert "n" in result.summary
    assert "win_rate" in result.summary
