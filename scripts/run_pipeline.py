#!/usr/bin/env python3
"""Run the full pipeline runner (strategy → risk → sim broker → reducers)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_demo.engine.bar_feed import BarFeed
from quant_demo.runner.config import RunnerConfig
from quant_demo.runner.pipeline_runner import run_pipeline
from quant_demo.runner.strategy_factory import build_strategy

DATA = ROOT / "data" / "synthetic" / "demo_bars.parquet"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run modular pipeline backtest")
    parser.add_argument("--strategy", choices=["sma_crossover", "ml_pipeline"], default="sma_crossover")
    parser.add_argument("--data", type=Path, default=DATA)
    args = parser.parse_args()

    if not args.data.exists():
        print("Synthetic data not found. Run: python scripts/generate_synthetic_data.py")
        sys.exit(1)

    cfg = RunnerConfig(
        data_path=args.data,
        strategy_name=args.strategy,
        use_ml_pipeline=args.strategy == "ml_pipeline",
    )
    strategy = build_strategy(cfg)
    feed = BarFeed.from_parquet(args.data)
    result = run_pipeline(strategy, feed, cfg)
    result.print_summary()


if __name__ == "__main__":
    main()
