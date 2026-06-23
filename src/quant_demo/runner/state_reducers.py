"""Pure TradingState reducers — no I/O, fully testable offline."""

from __future__ import annotations

import dataclasses
from typing import Optional

from quant_demo.events import FillLeg, OrderCommand, OrderDone, OrderSide, OrderStatusReason
from quant_demo.lifecycle import OrderRole, PositionGroupStatus, assert_transition
from quant_demo.state import OrderEntry, PositionGroup, TradingState


def apply_command(cmd: OrderCommand, state: TradingState) -> TradingState:
    """Register a newly submitted entry order; create its PositionGroup."""
    group_id = cmd.position_group_id or cmd.signal_id
    entry = OrderEntry(
        client_order_id=cmd.client_order_id,
        symbol=cmd.symbol,
        qty=cmd.qty,
        side=cmd.side.value,
        signal_id=cmd.signal_id,
        position_group_id=group_id,
        order_role=OrderRole.ENTRY,
    )
    group = PositionGroup(
        group_id=group_id,
        signal_id=cmd.signal_id,
        symbol=cmd.symbol,
        qty=cmd.qty,
        entry_client_order_id=cmd.client_order_id,
        oca_group=cmd.oca_group or group_id,
    )
    return dataclasses.replace(
        state,
        open_orders={**state.open_orders, cmd.client_order_id: entry},
        position_groups={**state.position_groups, group_id: group},
    )


def apply_bracket_commands(
    tp_cmd: OrderCommand,
    sl_cmd: OrderCommand,
    group_id: str,
    entry_price: float,
    state: TradingState,
) -> TradingState:
    """Register TP/SL legs and transition group to ENTRY_FILLED."""
    tp_entry = OrderEntry(
        client_order_id=tp_cmd.client_order_id,
        symbol=tp_cmd.symbol,
        qty=tp_cmd.qty,
        side=tp_cmd.side.value,
        signal_id=tp_cmd.signal_id,
        position_group_id=group_id,
        order_role=OrderRole.TP,
    )
    sl_entry = OrderEntry(
        client_order_id=sl_cmd.client_order_id,
        symbol=sl_cmd.symbol,
        qty=sl_cmd.qty,
        side=sl_cmd.side.value,
        signal_id=sl_cmd.signal_id,
        position_group_id=group_id,
        order_role=OrderRole.SL,
    )
    new_orders = {
        **state.open_orders,
        tp_cmd.client_order_id: tp_entry,
        sl_cmd.client_order_id: sl_entry,
    }
    group = state.position_groups.get(group_id)
    if group is not None:
        assert_transition(group.status, PositionGroupStatus.ENTRY_FILLED)
        new_groups = dict(state.position_groups)
        new_groups[group_id] = dataclasses.replace(
            group,
            tp_client_order_id=tp_cmd.client_order_id,
            sl_client_order_id=sl_cmd.client_order_id,
            entry_price=entry_price,
            tp_price=tp_cmd.limit_price or 0.0,
            sl_price=sl_cmd.stop_price or 0.0,
            status=PositionGroupStatus.ENTRY_FILLED,
        )
        return dataclasses.replace(state, open_orders=new_orders, position_groups=new_groups)
    return dataclasses.replace(state, open_orders=new_orders)


def apply_fill(fill: FillLeg, state: TradingState) -> TradingState:
    """Update position from a fill; record entry price on bracket group."""
    sign = 1.0 if fill.side == OrderSide.BUY else -1.0
    new_qty = state.position_qty + sign * fill.qty
    new_groups = dict(state.position_groups)

    entry = state.open_orders.get(fill.client_order_id)
    if entry is not None and entry.order_role == OrderRole.ENTRY:
        group = new_groups.get(entry.position_group_id)
        if group is not None:
            new_groups[entry.position_group_id] = dataclasses.replace(
                group, entry_price=fill.price
            )

    return dataclasses.replace(
        state,
        position_qty=new_qty,
        position_groups=new_groups,
        last_update=fill.timestamp,
    )


def apply_done(done: OrderDone, state: TradingState) -> TradingState:
    """Remove terminal order; update bracket group status."""
    coid = done.client_order_id
    if not coid:
        return state

    entry = state.open_orders.get(coid)
    new_orders = {k: v for k, v in state.open_orders.items() if k != coid}
    new_groups = dict(state.position_groups)
    new_outcomes = list(state.reconcile_outcomes)

    if entry is not None:
        gid = entry.position_group_id
        group = new_groups.get(gid)
        if group is not None:
            if entry.order_role == OrderRole.ENTRY and done.reason != OrderStatusReason.FILLED:
                assert_transition(group.status, PositionGroupStatus.CLOSED_CANCEL)
                new_groups[gid] = dataclasses.replace(
                    group, status=PositionGroupStatus.CLOSED_CANCEL, outcome="CANCEL"
                )
            elif entry.order_role == OrderRole.TP and done.reason == OrderStatusReason.FILLED:
                assert_transition(group.status, PositionGroupStatus.CLOSED_TP)
                new_groups[gid] = dataclasses.replace(
                    group, status=PositionGroupStatus.CLOSED_TP, outcome="TP"
                )
                new_outcomes.append("TP")
            elif entry.order_role == OrderRole.SL and done.reason == OrderStatusReason.FILLED:
                assert_transition(group.status, PositionGroupStatus.CLOSED_SL)
                new_groups[gid] = dataclasses.replace(
                    group, status=PositionGroupStatus.CLOSED_SL, outcome="SL"
                )
                new_outcomes.append("SL")

    return dataclasses.replace(
        state,
        open_orders=new_orders,
        position_groups=new_groups,
        reconcile_outcomes=new_outcomes,
    )


def close_group_timeout(group_id: str, state: TradingState) -> TradingState:
    """Force-close a group at session end (flatten path)."""
    group = state.position_groups.get(group_id)
    if group is None:
        return state
    assert_transition(group.status, PositionGroupStatus.CLOSED_TIMEOUT)
    new_groups = dict(state.position_groups)
    new_groups[group_id] = dataclasses.replace(
        group, status=PositionGroupStatus.CLOSED_TIMEOUT, outcome="TIMEOUT"
    )
    return dataclasses.replace(state, position_groups=new_groups)
