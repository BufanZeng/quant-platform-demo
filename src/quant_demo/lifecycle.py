"""
Bracket order lifecycle — explicit state machine for position groups.

Industry-standard bracket flow (entry limit → fill → OCA TP/SL → terminal).
States and transitions are common quant infrastructure; safe to publish.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet, Mapping


class PositionGroupStatus(str, Enum):
    """Lifecycle states for one bracket attempt (entry + TP + SL)."""

    ENTRY_PENDING = "ENTRY_PENDING"   # entry limit working; bracket not placed
    ENTRY_FILLED = "ENTRY_FILLED"     # in position; TP + SL active (OCA group)
    CLOSED_TP = "CLOSED_TP"           # take-profit filled; SL auto-cancelled
    CLOSED_SL = "CLOSED_SL"           # stop-loss filled; TP auto-cancelled
    CLOSED_CANCEL = "CLOSED_CANCEL"   # entry cancelled/rejected before fill
    CLOSED_TIMEOUT = "CLOSED_TIMEOUT" # force-flat (session end / kill switch)


class OrderRole(str, Enum):
    ENTRY = "entry"
    TP = "tp"
    SL = "sl"


TERMINAL_STATUSES: FrozenSet[PositionGroupStatus] = frozenset(
    {
        PositionGroupStatus.CLOSED_TP,
        PositionGroupStatus.CLOSED_SL,
        PositionGroupStatus.CLOSED_CANCEL,
        PositionGroupStatus.CLOSED_TIMEOUT,
    }
)

# Valid transitions: from_status -> {allowed_to_statuses}
VALID_TRANSITIONS: Mapping[PositionGroupStatus, FrozenSet[PositionGroupStatus]] = {
    PositionGroupStatus.ENTRY_PENDING: frozenset(
        {
            PositionGroupStatus.ENTRY_FILLED,
            PositionGroupStatus.CLOSED_CANCEL,
            PositionGroupStatus.CLOSED_TIMEOUT,
        }
    ),
    PositionGroupStatus.ENTRY_FILLED: frozenset(
        {
            PositionGroupStatus.CLOSED_TP,
            PositionGroupStatus.CLOSED_SL,
            PositionGroupStatus.CLOSED_TIMEOUT,
        }
    ),
    PositionGroupStatus.CLOSED_TP: frozenset(),
    PositionGroupStatus.CLOSED_SL: frozenset(),
    PositionGroupStatus.CLOSED_CANCEL: frozenset(),
    PositionGroupStatus.CLOSED_TIMEOUT: frozenset(),
}


class InvalidTransition(ValueError):
    """Raised when a position group state transition is not allowed."""


def can_transition(from_status: PositionGroupStatus, to_status: PositionGroupStatus) -> bool:
    return to_status in VALID_TRANSITIONS.get(from_status, frozenset())


def assert_transition(from_status: PositionGroupStatus, to_status: PositionGroupStatus) -> None:
    if not can_transition(from_status, to_status):
        raise InvalidTransition(f"{from_status.value} → {to_status.value} is not allowed")
