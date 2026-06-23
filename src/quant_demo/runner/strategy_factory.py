"""Factory — builds strategy + model components from runner config."""

from __future__ import annotations

from quant_demo.runner.config import RunnerConfig
from quant_demo.strategies.ml_pipeline_strategy import MLPipelineStrategy
from quant_demo.strategies.sma_crossover import SMACrossoverStrategy
from quant_demo.strategy_protocol import Strategy


def build_strategy(cfg: RunnerConfig) -> Strategy:
    if cfg.use_ml_pipeline or cfg.strategy_name == "ml_pipeline":
        return MLPipelineStrategy()
    return SMACrossoverStrategy()
