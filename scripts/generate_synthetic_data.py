#!/usr/bin/env python3
"""Generate synthetic OHLCV bars and a labeled ML table."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic"


def generate_bars(n_bars: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    price = 100.0
    rows = []
    calendar = pd.date_range("2025-01-02", "2025-05-31", freq="B")

    for i in range(n_bars):
        day = calendar[i % len(calendar)]
        bar_ts = day + pd.Timedelta(minutes=30 + 5 * (i % 78))
        ret = rng.normal(0, 0.3)
        open_ = price
        close = max(1.0, price + ret)
        high = max(open_, close) + abs(rng.normal(0, 0.1))
        low = min(open_, close) - abs(rng.normal(0, 0.1))
        rows.append(
            {
                "symbol": "DEMO",
                "timeframe": "5m",
                "timestamp": bar_ts,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": int(rng.integers(100, 1000)),
                "source": "synthetic",
            }
        )
        price = close

    return pd.DataFrame(rows)


def generate_ml_table(bars: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    closes = bars["close"].values
    fast = pd.Series(closes).rolling(5).mean()
    slow = pd.Series(closes).rolling(20).mean()
    mom = pd.Series(closes).diff(5)
    vol = pd.Series(closes).rolling(20).std()

    df = pd.DataFrame(
        {
            "audit_date": bars["timestamp"].dt.strftime("%Y-%m-%d"),
            "id_signal": [f"sig-{i:04d}" for i in range(len(bars))],
            "feature_close": closes,
            "feature_sma_fast": fast,
            "feature_sma_slow": slow,
            "feature_momentum": mom,
            "feature_volatility": vol,
        }
    )
    df = df.dropna().reset_index(drop=True)
    score = (
        0.4 * (df["feature_sma_fast"] - df["feature_sma_slow"])
        + 0.3 * df["feature_momentum"]
        - 0.1 * df["feature_volatility"]
    )
    prob = 1 / (1 + np.exp(-score / df["feature_volatility"].clip(lower=0.1)))
    df["target_win"] = (rng.random(len(df)) < prob).astype(int)
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bars", type=int, default=1200)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    bars = generate_bars(n_bars=args.bars)
    bars.to_parquet(OUT / "demo_bars.parquet", index=False)
    bars.to_csv(OUT / "demo_bars.csv", index=False)

    ml_table = generate_ml_table(bars)
    ml_table.to_parquet(OUT / "ml_demo_table.parquet", index=False)

    print(f"Wrote {len(bars)} bars → {OUT / 'demo_bars.parquet'}")
    print(f"Wrote {len(ml_table)} ML rows → {OUT / 'ml_demo_table.parquet'}")


if __name__ == "__main__":
    main()
