# Quant Platform Demo

A **public, sanitized showcase** of an event-driven quantitative trading platform.
This repository demonstrates system design, layered architecture, and ML pipeline
patterns — without proprietary signal logic, broker credentials, or production data.

> **Note:** The production system (live broker integration, proprietary strategies,
> and labeled datasets) is private. This repo is the architecture and engineering
> story you can share on a resume or in interviews.

## What this demonstrates

| Layer | Demo implementation |
|-------|---------------------|
| Event spine | `BarClosed` → strategy → risk → simulated execution |
| Strategy plug-in | `Strategy` protocol with a placeholder SMA crossover |
| ML boundary | `FeatureRow` → `ModelLayer` → `Prediction` → `TradeSpec` |
| Risk gate | Pure function: intent → allow/deny + `OrderCommand` |
| ML ops | Config-driven training, temporal split, versioned model registry |
| Tests | Risk engine, pipeline layers, end-to-end backtest smoke |

## Architecture (one diagram)

```
BarClosed (synthetic CSV or parquet replay)
  │
  ▼ Factor / feature builder     strategies/sma_crossover.py
  │  rolling indicators, session context
  │
  ▼ FeatureRow                   engine/features.py
  │  flat, parquet-serialisable
  │
  ▼ ModelLayer (Protocol)        engine/model_layer.py
  │  Demo: ThresholdClassifier (rule-based)
  │  Prod pattern: swap in trained sklearn / LightGBM
  │
  ▼ Prediction                   direction + confidence only
  │
  ▼ TradeConstructor             engine/trade_constructor.py
  │  structural SL/TP from config (not from the model)
  │
  ▼ Risk Gate                    risk.py
  │  position caps, daily loss, kill switch
  │
  ▼ Simulated execution          engine/backtest.py
```

Backtest and live trading share the **same event types and pipeline layers**;
only the data adapter changes (parquet replay vs broker stream).

## Quick start

```bash
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

# Generate synthetic OHLCV bars
python scripts/generate_synthetic_data.py

# Run placeholder strategy backtest
python scripts/run_backtest.py

# Train a demo ML model on synthetic labels
python scripts/ml/run_pipeline.py --config configs/ml_demo.json

# Run tests
pytest
```

## Project layout

```
quant-platform-demo/
├── docs/
│   ├── architecture.md      # system design (read this first)
│   └── ml-pipeline.md       # offline training + registry design
├── src/quant_demo/
│   ├── events.py            # domain events
│   ├── state.py             # market vs trading state
│   ├── risk.py              # pure risk engine
│   ├── strategy_protocol.py # Strategy plug-in contract
│   ├── engine/              # backtest, features, model layer
│   ├── strategies/          # demo strategies (not proprietary)
│   └── ml/                  # versioned training pipeline
├── scripts/
│   ├── generate_synthetic_data.py
│   ├── run_backtest.py
│   └── ml/run_pipeline.py
├── configs/ml_demo.json
├── data/synthetic/          # generated demo bars + ML table
└── tests/
```

## What is intentionally excluded

- Proprietary entry/exit rules and factor definitions
- Real market data and performance metrics
- Broker API credentials and live execution code
- Production configs and labeled datasets

## Documentation

- [System architecture](docs/architecture.md)
- [ML pipeline design](docs/ml-pipeline.md)

## License

MIT — see [LICENSE](LICENSE).
