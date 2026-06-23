"""
Simulated broker adapter — produces FillLeg / OrderDone for the runner.

Mirrors live IBKR bracket semantics (OCA: one protective leg fill cancels the other).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from quant_demo.events import (
    BarClosed,
    OrderCommand,
    OrderCommandKind,
    OrderDone,
    OrderSide,
    OrderStatusReason,
    FillLeg,
    TradeDirection,
)
from quant_demo.lifecycle import OrderRole


@dataclass
class WorkingOrder:
    cmd: OrderCommand
    group_id: str
    role: OrderRole
    tp_price: float = 0.0
    sl_price: float = 0.0
    direction: TradeDirection = TradeDirection.LONG


@dataclass
class SimBroker:
    """Stateful simulated execution — the live adapter swap-in point."""

    working: List[WorkingOrder] = field(default_factory=list)
    events: List[object] = field(default_factory=list)

    def submit(self, cmd: OrderCommand, meta: dict) -> None:
        if cmd.kind == OrderCommandKind.SUBMIT_LIMIT:
            self.working.append(
                WorkingOrder(
                    cmd=cmd,
                    group_id=cmd.position_group_id,
                    role=OrderRole.ENTRY,
                    tp_price=float(meta.get("tp", 0.0)),
                    sl_price=float(meta.get("sl", 0.0)),
                    direction=TradeDirection(meta.get("direction", "LONG")),
                )
            )

    def on_bar(self, bar: BarClosed) -> List[object]:
        """Scan working orders against bar OHLC; emit fills and terminal events."""
        emitted: List[object] = []
        still_working: List[WorkingOrder] = []

        for order in self.working:
            events = self._process_order(order, bar)
            if events:
                emitted.extend(events)
            else:
                still_working.append(order)

        self.working = still_working
        self.events.extend(emitted)
        return emitted

    def _process_order(self, order: WorkingOrder, bar: BarClosed) -> List[object]:
        cmd = order.cmd
        ts = bar.timestamp

        if order.role == OrderRole.ENTRY:
            if not self._entry_touched(bar, cmd, order.direction):
                return []
            fill = FillLeg(
                fill_id=f"fill-{uuid.uuid4().hex[:8]}",
                client_order_id=cmd.client_order_id,
                symbol=cmd.symbol,
                side=cmd.side,
                qty=cmd.qty,
                price=cmd.limit_price or bar.close,
                timestamp=ts,
            )
            done = OrderDone(
                client_order_id=cmd.client_order_id,
                symbol=cmd.symbol,
                reason=OrderStatusReason.FILLED,
                timestamp=ts,
            )
            # Place protective legs (OCA group)
            exit_side = OrderSide.SELL if cmd.side == OrderSide.BUY else OrderSide.BUY
            tp_cmd = OrderCommand(
                client_order_id=f"{order.group_id}-tp",
                symbol=cmd.symbol,
                side=exit_side,
                kind=OrderCommandKind.SUBMIT_LIMIT,
                qty=cmd.qty,
                limit_price=order.tp_price,
                signal_id=cmd.signal_id,
                position_group_id=order.group_id,
                oca_group=order.group_id,
            )
            sl_cmd = OrderCommand(
                client_order_id=f"{order.group_id}-sl",
                symbol=cmd.symbol,
                side=exit_side,
                kind=OrderCommandKind.SUBMIT_STOP,
                qty=cmd.qty,
                stop_price=order.sl_price,
                signal_id=cmd.signal_id,
                position_group_id=order.group_id,
                oca_group=order.group_id,
            )
            self.working.extend(
                [
                    WorkingOrder(tp_cmd, order.group_id, OrderRole.TP, direction=order.direction),
                    WorkingOrder(sl_cmd, order.group_id, OrderRole.SL, direction=order.direction),
                ]
            )
            return [fill, done, tp_cmd, sl_cmd]

        if order.role == OrderRole.TP and cmd.limit_price is not None:
            if self._tp_hit(bar, order.direction, cmd.limit_price):
                return self._close_leg(cmd, cmd.limit_price, ts, OrderRole.TP)
            return []

        if order.role == OrderRole.SL and cmd.stop_price is not None:
            if self._sl_hit(bar, order.direction, cmd.stop_price):
                return self._close_leg(cmd, cmd.stop_price, ts, OrderRole.SL)
            return []

        return []

    def _close_leg(
        self, cmd: OrderCommand, price: float, ts: datetime, role: OrderRole
    ) -> List[object]:
        # OCA: cancel sibling protective leg
        sibling_role = OrderRole.SL if role == OrderRole.TP else OrderRole.TP
        sibling_id = f"{cmd.position_group_id}-{sibling_role.value}"
        self.working = [w for w in self.working if w.cmd.client_order_id != sibling_id]

        fill = FillLeg(
            fill_id=f"fill-{uuid.uuid4().hex[:8]}",
            client_order_id=cmd.client_order_id,
            symbol=cmd.symbol,
            side=cmd.side,
            qty=cmd.qty,
            price=price,
            timestamp=ts,
        )
        done = OrderDone(
            client_order_id=cmd.client_order_id,
            symbol=cmd.symbol,
            reason=OrderStatusReason.FILLED,
            timestamp=ts,
        )
        cancel = OrderDone(
            client_order_id=sibling_id,
            symbol=cmd.symbol,
            reason=OrderStatusReason.CANCELLED,
            timestamp=ts,
        )
        return [fill, done, cancel]

    @staticmethod
    def _entry_touched(bar: BarClosed, cmd: OrderCommand, direction: TradeDirection) -> bool:
        price = cmd.limit_price or bar.close
        if direction == TradeDirection.LONG:
            return bar.low <= price
        return bar.high >= price

    @staticmethod
    def _tp_hit(bar: BarClosed, direction: TradeDirection, tp: float) -> bool:
        return bar.high >= tp if direction == TradeDirection.LONG else bar.low <= tp

    @staticmethod
    def _sl_hit(bar: BarClosed, direction: TradeDirection, sl: float) -> bool:
        return bar.low <= sl if direction == TradeDirection.LONG else bar.high >= sl
