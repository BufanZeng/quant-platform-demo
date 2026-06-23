"""Risk engine unit tests."""

from quant_demo.events import StrategyIntent, TradeDirection
from quant_demo.risk import Allow, Deny, RiskConfig, evaluate
from quant_demo.state import TradingState


def test_allows_valid_intent():
    intent = StrategyIntent("s1", "DEMO", TradeDirection.LONG, qty_hint=1.0)
    decision = evaluate(intent, TradingState(), RiskConfig())
    assert isinstance(decision, Allow)
    assert len(decision.commands) == 1


def test_denies_kill_switch():
    intent = StrategyIntent("s1", "DEMO", TradeDirection.LONG)
    decision = evaluate(intent, TradingState(), RiskConfig(kill_switch=True))
    assert isinstance(decision, Deny)
    assert decision.reason == "kill_switch"


def test_denies_max_position():
    intent = StrategyIntent("s1", "DEMO", TradeDirection.LONG, qty_hint=5.0)
    state = TradingState(position_qty=8.0)
    decision = evaluate(intent, state, RiskConfig(max_position_qty=10.0))
    assert isinstance(decision, Deny)
    assert decision.reason == "max_position"


def test_denies_daily_loss():
    intent = StrategyIntent("s1", "DEMO", TradeDirection.LONG)
    state = TradingState(daily_pnl=-600.0)
    decision = evaluate(intent, state, RiskConfig(max_daily_loss=-500.0))
    assert isinstance(decision, Deny)
    assert decision.reason == "daily_loss_limit"
