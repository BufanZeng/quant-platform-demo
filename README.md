# Quant Platform Demo

A **public, sanitized showcase** of an event-driven quantitative trading platform.
This repository demonstrates system design, layered architecture, state machines,
and ML pipeline patterns — without proprietary signal logic or production data.

> **Note:** The production system (live IBKR integration, proprietary strategies,
> and labeled datasets) is private. This repo is the architecture story for
> resumes and technical interviews.

## What a tech lead should see here

| Design choice | Where to look |
|---------------|---------------|
| **Bracket state machine** | `src/quant_demo/lifecycle.py`, `docs/state-machines.md` |
| **Runner / orchestration shell** | `src/quant_demo/runner/pipeline_runner.py` |
| **Pure state reducers** | `src/quant_demo/runner/state_reducers.py` |
| **Broker adapter swap point** | `src/quant_demo/execution/sim_broker.py` |
| **Protocol-based plug-ins** | `strategy_protocol.py`, `engine/model_layer.py` |
| **Risk as sole order gate** | `src/quant_demo/risk.py` |
| **Broker-wins reconciliation** | `src/quant_demo/runner/reconciliation.py` |
| **ML ops** | `src/quant_demo/ml/`, `configs/ml_demo.json` |

## Architecture

```
BarClosed
  │
  ▼ Strategy (plug-in)           strategies/sma_crossover.py | ml_pipeline_strategy.py
  │  FeatureRow → ModelLayer → Prediction → TradeSpec
  │
  ▼ Risk gate                    risk.py  (only layer that emits OrderCommand)
  │
  ▼ Execution adapter            execution/sim_broker.py  (live: IBKR)
  │  FillLeg / OrderDone → state reducers
  │
  ▼ TradingState projection      runner/state_reducers.py
  │  PositionGroup state machine (ENTRY_PENDING → … → CLOSED_*)
  │
  ▼ Reconciliation monitors      runner/reconciliation.py
```

Backtest and live share the **same runner and event types**; only the execution
adapter changes.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

python scripts/generate_synthetic_data.py

# Full pipeline runner (recommended)
python scripts/run_pipeline.py
python scripts/run_pipeline.py --strategy ml_pipeline

# ML training
python scripts/ml/run_pipeline.py --config configs/ml_demo.json

pytest
```

## Project layout

```
quant-platform-demo/
├── docs/
│   ├── architecture.md
│   ├── state-machines.md      # bracket lifecycle diagram
│   └── ml-pipeline.md
├── src/quant_demo/
│   ├── lifecycle.py           # PositionGroupStatus + VALID_TRANSITIONS
│   ├── events.py              # immutable domain events
│   ├── state.py               # MarketState vs TradingState
│   ├── risk.py
│   ├── runner/
│   │   ├── pipeline_runner.py # orchestration shell
│   │   ├── state_reducers.py
│   │   ├── reconciliation.py
│   │   ├── strategy_factory.py
│   │   └── config.py
│   ├── execution/
│   │   └── sim_broker.py      # simulated OCA brackets
│   ├── engine/                # features, model layer, trade constructor
│   ├── strategies/
│   └── ml/
└── tests/
    ├── test_state_machine.py
    ├── test_state_reducers.py
    └── test_pipeline_runner.py
```

## Documentation

- [System architecture](docs/architecture.md)
- [Bracket state machines](docs/state-machines.md)
- [ML pipeline design](docs/ml-pipeline.md)

## License

MIT — see [LICENSE](LICENSE).
