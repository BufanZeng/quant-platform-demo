"""Generic bar-stream backtest runner with simulated fills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pandas as pd

from quant_demo.engine.bar_feed import BarFeed
from quant_demo.events import BarClosed, TradeDirection
from quant_demo.strategy_protocol import Strategy


@dataclass
class FillResult:
    filled: bool
    exit_reason: Literal["tp", "sl", "session_end", "no_meta"] = "no_meta"
    net_pnl_pts: float = 0.0


@dataclass
class BacktestResult:
    strategy_name: str
    trades: pd.DataFrame
    summary: dict

    def print_summary(self) -> None:
        s = self.summary
        print(f"Strategy : {self.strategy_name}")
        print(f"Trades   : {s['n']} (filled: {s['filled']})")
        print(f"Win rate : {s['win_rate']:.1%}")
        print(f"Total PnL: {s['total_pnl_pts']:+.2f} pts")


def _simulate_fill(bar: BarClosed, intent_meta: dict) -> FillResult:
    entry = intent_meta.get("entry_price")
    sl = intent_meta.get("sl")
    tp = intent_meta.get("tp")
    if entry is None or sl is None or tp is None:
        return FillResult(filled=False, exit_reason="no_meta")

    direction = intent_meta.get("direction", "LONG")
    if direction in (TradeDirection.LONG, "LONG", "up"):
        if bar.low <= sl:
            return FillResult(True, "sl", sl - entry)
        if bar.high >= tp:
            return FillResult(True, "tp", tp - entry)
    else:
        if bar.high >= sl:
            return FillResult(True, "sl", entry - sl)
        if bar.low <= tp:
            return FillResult(True, "tp", entry - tp)

    return FillResult(True, "session_end", bar.close - entry if direction in ("LONG", "up") else entry - bar.close)


def run_backtest(strategy: Strategy, feed: BarFeed) -> BacktestResult:
    records: list[dict] = []
    pending: dict | None = None

    for bar in feed:
        out = strategy.on_bar(bar)
        for intent in out.intents:
            meta = dict(intent.metadata)
            meta["direction"] = intent.direction.value
            pending = {
                "signal_id": intent.signal_id,
                "bar_ts": bar.timestamp,
                "side": intent.direction.value,
                **meta,
            }

        if pending is not None:
            result = _simulate_fill(bar, pending)
            if result.filled and result.exit_reason != "no_meta":
                records.append(
                    {
                        "signal_id": pending["signal_id"],
                        "side": pending["side"],
                        "entry_price": pending.get("entry_price"),
                        "sl": pending.get("sl"),
                        "tp": pending.get("tp"),
                        "bar_ts": pending["bar_ts"],
                        "exit_reason": result.exit_reason,
                        "net_pnl_pts": result.net_pnl_pts,
                    }
                )
                pending = None

    trades = pd.DataFrame(records)
    if trades.empty:
        summary = {"n": 0, "filled": 0, "win_rate": 0.0, "total_pnl_pts": 0.0}
    else:
        wins = (trades["net_pnl_pts"] > 0).sum()
        summary = {
            "n": len(trades),
            "filled": len(trades),
            "win_rate": wins / len(trades),
            "total_pnl_pts": float(trades["net_pnl_pts"].sum()),
        }

    return BacktestResult(strategy_name=strategy.name, trades=trades, summary=summary)
