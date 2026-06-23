"""End-to-end backtest smoke test."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from quant_demo.engine.backtest import run_backtest
from quant_demo.engine.bar_feed import BarFeed
from quant_demo.strategies.sma_crossover import SMACrossoverStrategy


def _synthetic_bars(n: int = 80) -> pd.DataFrame:
    rows = []
    price = 100.0
    for i in range(n):
        price += 0.1 if i % 10 < 6 else -0.05
        rows.append(
            {
                "symbol": "DEMO",
                "timeframe": "5m",
                "timestamp": datetime(2025, 1, 2, 9, 30) + pd.Timedelta(minutes=5 * i),
                "open": price,
                "high": price + 0.5,
                "low": price - 0.5,
                "close": price,
                "volume": 100,
                "source": "test",
            }
        )
    return pd.DataFrame(rows)


def test_backtest_runs_without_error():
    feed = BarFeed(_synthetic_bars())
    result = run_backtest(SMACrossoverStrategy(fast=3, slow=10), feed)
    assert result.strategy_name == "sma_crossover"
    assert "n" in result.summary
