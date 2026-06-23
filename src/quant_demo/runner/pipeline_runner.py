"""
Pipeline runner — stitches modular components into one event loop.

    BarFeed → Strategy → Risk → Execution → State reducers → Reconciliation

Live production swaps ``SimBroker`` for an IBKR adapter; orchestration stays identical.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Set

import pandas as pd

from quant_demo.engine.bar_feed import BarFeed
from quant_demo.engine.features import FeatureRow
from quant_demo.events import FillLeg, OrderCommand, OrderDone
from quant_demo.execution.sim_broker import SimBroker
from quant_demo.risk import Allow, Deny, evaluate
from quant_demo.runner.config import RunnerConfig
from quant_demo.runner.reconciliation import check_sl_ratio
from quant_demo.runner.state_reducers import (
    apply_bracket_commands,
    apply_command,
    apply_done,
    apply_fill,
)
from quant_demo.state import MarketState, TradingState, reduce_market_state
from quant_demo.strategy_protocol import Strategy


@dataclass
class PipelineRunResult:
    strategy_name: str
    trades: pd.DataFrame
    summary: dict
    feature_log: List[FeatureRow] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    event_count: int = 0

    def print_summary(self) -> None:
        s = self.summary
        print(f"Strategy    : {self.strategy_name}")
        print(f"Trades      : {s['n']} closed brackets")
        print(f"Win rate    : {s['win_rate']:.1%}")
        print(f"Total PnL   : {s['total_pnl_pts']:+.2f} pts")
        print(f"Events      : {self.event_count}")
        if self.alerts:
            print(f"Alerts      : {len(self.alerts)}")


def run_pipeline(strategy: Strategy, feed: BarFeed, cfg: RunnerConfig) -> PipelineRunResult:
    market = MarketState()
    trading = TradingState()
    broker = SimBroker()
    feature_log: List[FeatureRow] = []
    alerts: List[str] = []
    closed_trades: List[dict] = []
    recorded_groups: Set[str] = set()
    event_count = 0
    pending_tp_sl: dict[str, OrderCommand] = {}

    for bar in feed:
        market = reduce_market_state(market, bar)
        trading.risk_counters["orders_this_bar"] = 0

        out = strategy.on_bar(bar)
        if hasattr(strategy, "feature_log"):
            feature_log = list(strategy.feature_log)  # type: ignore[attr-defined]

        for intent in out.intents:
            decision = evaluate(intent, trading, cfg.risk)
            if isinstance(decision, Deny):
                alerts.append(f"risk_deny:{decision.reason}:{intent.signal_id}")
                continue

            meta = dict(intent.metadata)
            meta["direction"] = intent.direction.value
            for cmd in decision.commands:
                group_id = f"grp-{intent.signal_id}"
                enriched = OrderCommand(
                    client_order_id=cmd.client_order_id,
                    symbol=cmd.symbol,
                    side=cmd.side,
                    kind=cmd.kind,
                    qty=cmd.qty,
                    limit_price=cmd.limit_price,
                    signal_id=cmd.signal_id,
                    position_group_id=group_id,
                    oca_group=group_id,
                )
                trading = apply_command(enriched, trading)
                broker.submit(enriched, meta)
                trading.risk_counters["orders_this_bar"] = (
                    trading.risk_counters.get("orders_this_bar", 0) + 1
                )
                event_count += 1

        for event in broker.on_bar(bar):
            event_count += 1
            if isinstance(event, FillLeg):
                trading = apply_fill(event, trading)
            elif isinstance(event, OrderCommand):
                gid = event.position_group_id
                if event.client_order_id.endswith("-tp"):
                    pending_tp_sl[f"{gid}:tp"] = event
                elif event.client_order_id.endswith("-sl"):
                    pending_tp_sl[f"{gid}:sl"] = event
                tp = pending_tp_sl.get(f"{gid}:tp")
                sl = pending_tp_sl.get(f"{gid}:sl")
                if tp and sl:
                    group = trading.position_groups.get(gid)
                    entry_px = group.entry_price if group and group.entry_price else bar.close
                    trading = apply_bracket_commands(tp, sl, gid, entry_px, trading)
                    pending_tp_sl.pop(f"{gid}:tp", None)
                    pending_tp_sl.pop(f"{gid}:sl", None)
            elif isinstance(event, OrderDone):
                trading = apply_done(event, trading)
                for group in trading.position_groups.values():
                    if group.group_id in recorded_groups:
                        continue
                    if group.outcome in ("TP", "SL") and group.entry_price:
                        pnl = (
                            abs(group.tp_price - group.entry_price)
                            if group.outcome == "TP"
                            else -abs(group.entry_price - group.sl_price)
                        )
                        closed_trades.append(
                            {
                                "group_id": group.group_id,
                                "signal_id": group.signal_id,
                                "outcome": group.outcome,
                                "status": group.status.value,
                                "entry_price": group.entry_price,
                                "net_pnl_pts": pnl * cfg.point_value,
                            }
                        )
                        recorded_groups.add(group.group_id)

        alert = check_sl_ratio(trading, cfg.reconcile_sl_window, cfg.reconcile_sl_threshold)
        if alert is not None:
            alerts.append(alert.message)

    trades = pd.DataFrame(closed_trades)
    if trades.empty:
        summary = {"n": 0, "win_rate": 0.0, "total_pnl_pts": 0.0}
    else:
        wins = (trades["net_pnl_pts"] > 0).sum()
        summary = {
            "n": len(trades),
            "win_rate": wins / len(trades),
            "total_pnl_pts": float(trades["net_pnl_pts"].sum()),
        }

    return PipelineRunResult(
        strategy_name=strategy.name,
        trades=trades,
        summary=summary,
        feature_log=feature_log,
        alerts=alerts,
        event_count=event_count,
    )
