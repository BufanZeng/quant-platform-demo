"""Broker-wins reconciliation checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from quant_demo.state import TradingState


@dataclass(frozen=True)
class ReconcileAlert:
    alert_type: str
    message: str
    internal_qty: float
    broker_qty: float


def check_position_drift(
    state: TradingState,
    broker_position_qty: float,
    tolerance: float = 1e-6,
) -> Optional[ReconcileAlert]:
    """Return alert when internal position disagrees with broker snapshot."""
    if abs(state.position_qty - broker_position_qty) <= tolerance:
        return None
    return ReconcileAlert(
        alert_type="POSITION_DRIFT",
        message=(
            f"Internal position {state.position_qty} != broker {broker_position_qty}; "
            "broker wins — reconcile before new orders."
        ),
        internal_qty=state.position_qty,
        broker_qty=broker_position_qty,
    )


def check_sl_ratio(
    state: TradingState,
    window: int = 10,
    threshold: float = 0.7,
) -> Optional[ReconcileAlert]:
    """Rolling SL ratio guard — common live risk monitor."""
    outcomes = state.reconcile_outcomes
    if len(outcomes) < window:
        return None
    recent = outcomes[-window:]
    sl_count = recent.count("SL")
    tp_count = recent.count("TP")
    total = sl_count + tp_count
    if total == 0:
        return None
    ratio = sl_count / total
    if ratio <= threshold:
        return None
    return ReconcileAlert(
        alert_type="SL_RATIO_EXCEEDED",
        message=f"Last {total} closes: SL ratio {ratio:.0%} > {threshold:.0%}",
        internal_qty=state.position_qty,
        broker_qty=state.position_qty,
    )
