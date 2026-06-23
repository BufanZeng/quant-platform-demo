"""
Risk engine: StrategyIntent → OrderCommand or deny.

Only the risk engine may emit OrderCommand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from quant_demo.events import (
    OrderCommand,
    OrderCommandKind,
    OrderSide,
    StrategyIntent,
    TradeDirection,
)
from quant_demo.state import TradingState

__all__ = ["RiskConfig", "RiskDecision", "evaluate"]


@dataclass(frozen=True)
class RiskConfig:
    kill_switch: bool = False
    max_position_qty: float = 10.0
    max_open_orders: int = 3
    max_daily_loss: float | None = -500.0
    max_orders_per_bar: int | None = 2
    default_qty: float = 1.0


@dataclass(frozen=True)
class Allow:
    commands: List[OrderCommand]


@dataclass(frozen=True)
class Deny:
    reason: str


RiskDecision = Union[Allow, Deny]


def evaluate(
    intent: StrategyIntent,
    state: TradingState,
    config: RiskConfig,
) -> RiskDecision:
    if config.kill_switch:
        return Deny("kill_switch")

    qty = intent.qty_hint or config.default_qty
    signed = qty if intent.direction == TradeDirection.LONG else -qty
    new_position = state.position_qty + signed

    if abs(new_position) > config.max_position_qty:
        return Deny("max_position")

    if len(state.open_orders) >= config.max_open_orders:
        return Deny("max_open_orders")

    if config.max_daily_loss is not None and state.daily_pnl <= config.max_daily_loss:
        return Deny("daily_loss_limit")

    orders_this_bar = int(state.risk_counters.get("orders_this_bar", 0))
    if config.max_orders_per_bar is not None and orders_this_bar >= config.max_orders_per_bar:
        return Deny("max_orders_per_bar")

    side = OrderSide.BUY if intent.direction == TradeDirection.LONG else OrderSide.SELL
    entry_price = intent.metadata.get("entry_price")
    kind = OrderCommandKind.SUBMIT_LIMIT if entry_price is not None else OrderCommandKind.SUBMIT_MARKET

    cmd = OrderCommand(
        client_order_id=f"ord-{intent.signal_id}",
        symbol=intent.symbol,
        side=side,
        kind=kind,
        qty=qty,
        limit_price=float(entry_price) if entry_price is not None else None,
        signal_id=intent.signal_id,
        position_group_id=f"grp-{intent.signal_id}",
        oca_group=f"grp-{intent.signal_id}",
    )
    return Allow(commands=[cmd])
