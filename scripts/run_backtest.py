#!/usr/bin/env python3
"""Run a demo backtest on synthetic bars."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_demo.engine.backtest import run_backtest
from quant_demo.engine.bar_feed import BarFeed
from quant_demo.strategies.sma_crossover import SMACrossoverStrategy

DATA = ROOT / "data" / "synthetic" / "demo_bars.parquet"


def main() -> None:
    if not DATA.exists():
        print("Synthetic data not found. Run: python scripts/generate_synthetic_data.py")
        sys.exit(1)

    strategy = SMACrossoverStrategy()
    feed = BarFeed.from_parquet(DATA)
    result = run_backtest(strategy, feed)
    result.print_summary()
    print(f"Feature rows logged: {len(strategy.feature_log)}")


if __name__ == "__main__":
    main()
