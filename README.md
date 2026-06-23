# Quant Platform Demo

Public reference implementation of an event-driven futures trading platform.
Placeholder strategies and synthetic data only — proprietary signal logic and
live broker integration live in a private repo.

**→ [Architecture & design](docs/architecture.md)** — start here.

## Pipeline

```
Live data → Feature builder → ML layer → Trade construction → Risk engine → Execution
```

Backtest replays the same pipeline; only the data and execution adapters change.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

python scripts/generate_synthetic_data.py
python scripts/run_pipeline.py
python scripts/run_pipeline.py --strategy ml_pipeline
python scripts/ml/run_pipeline.py --config configs/ml_demo.json
pytest
```

## Layout

```
src/quant_demo/
├── lifecycle.py          # bracket state machine
├── events.py             # immutable domain events
├── state.py              # market vs trading state
├── risk.py
├── runner/               # pipeline_runner, reducers, reconciliation
├── execution/            # sim_broker (live adapter swap-in)
├── engine/               # features, model layer, trade constructor
├── strategies/
└── ml/                   # offline training + model registry
```

## License

MIT — see [LICENSE](LICENSE).
