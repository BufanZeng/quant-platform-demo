"""State machine transition tests."""

import pytest

from quant_demo.lifecycle import (
    InvalidTransition,
    PositionGroupStatus,
    assert_transition,
    can_transition,
)


def test_entry_pending_to_filled():
    assert can_transition(PositionGroupStatus.ENTRY_PENDING, PositionGroupStatus.ENTRY_FILLED)


def test_entry_pending_cannot_skip_to_tp():
    assert not can_transition(PositionGroupStatus.ENTRY_PENDING, PositionGroupStatus.CLOSED_TP)


def test_terminal_has_no_exits():
    for status in (
        PositionGroupStatus.CLOSED_TP,
        PositionGroupStatus.CLOSED_SL,
        PositionGroupStatus.CLOSED_CANCEL,
    ):
        assert not can_transition(status, PositionGroupStatus.ENTRY_PENDING)


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransition):
        assert_transition(PositionGroupStatus.CLOSED_TP, PositionGroupStatus.ENTRY_FILLED)
