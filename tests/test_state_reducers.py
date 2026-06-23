"""State reducer unit tests."""

import dataclasses
from datetime import datetime

from quant_demo.events import (
    FillLeg,
    OrderCommand,
    OrderCommandKind,
    OrderDone,
    OrderSide,
    OrderStatusReason,
)
from quant_demo.lifecycle import OrderRole, PositionGroupStatus
from quant_demo.runner.state_reducers import apply_bracket_commands, apply_command, apply_done, apply_fill
from quant_demo.state import OrderEntry, TradingState


def _entry_cmd(group_id: str = "grp-1") -> OrderCommand:
    return OrderCommand(
        client_order_id="entry-1",
        symbol="DEMO",
        side=OrderSide.BUY,
        kind=OrderCommandKind.SUBMIT_LIMIT,
        qty=1.0,
        limit_price=100.0,
        signal_id="sig-1",
        position_group_id=group_id,
        oca_group=group_id,
    )


def test_apply_command_creates_pending_group():
    state = apply_command(_entry_cmd(), TradingState())
    assert "entry-1" in state.open_orders
    assert state.position_groups["grp-1"].status == PositionGroupStatus.ENTRY_PENDING


def test_bracket_fill_transitions_to_entry_filled():
    state = apply_command(_entry_cmd(), TradingState())
    state = apply_fill(
        FillLeg("f1", "entry-1", "DEMO", OrderSide.BUY, 1.0, 100.0, datetime(2025, 1, 2)),
        state,
    )
    tp = OrderCommand("grp-1-tp", "DEMO", OrderSide.SELL, OrderCommandKind.SUBMIT_LIMIT, 1.0, limit_price=104.0, position_group_id="grp-1")
    sl = OrderCommand("grp-1-sl", "DEMO", OrderSide.SELL, OrderCommandKind.SUBMIT_STOP, 1.0, stop_price=98.0, position_group_id="grp-1")
    state = apply_bracket_commands(tp, sl, "grp-1", 100.0, state)
    assert state.position_groups["grp-1"].status == PositionGroupStatus.ENTRY_FILLED


def test_tp_done_closes_group():
    state = apply_command(_entry_cmd(), TradingState())
    group = state.position_groups["grp-1"]
    state.position_groups["grp-1"] = dataclasses.replace(
        group, status=PositionGroupStatus.ENTRY_FILLED
    )
    state.open_orders["grp-1-tp"] = OrderEntry(
        "grp-1-tp", "DEMO", 1.0, "SELL", position_group_id="grp-1", order_role=OrderRole.TP
    )
    state = apply_done(
        OrderDone("grp-1-tp", "DEMO", OrderStatusReason.FILLED, datetime(2025, 1, 2)),
        state,
    )
    assert state.position_groups["grp-1"].status == PositionGroupStatus.CLOSED_TP
    assert state.reconcile_outcomes[-1] == "TP"
