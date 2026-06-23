# ML pipeline design

Offline model training is a separate subsystem from the live runner. The live
system logs `FeatureRow` records; the ML pipeline trains on those parquets and
registers versioned models for deployment.

---

## Pipeline stages

```
Config JSON
    │
    ├── 1. Load & clean dataset
    ├── 2. Temporal split (train / val / test by date)
    ├── 3. Feature selection (optional)
    ├── 4. Train model
    ├── 5. Evaluate (classification metrics)
    └── 6. Register versioned artifact → models/v001/
```

Every run is fully reproducible from its config and produces:

```
models/v001/
├── model.pkl
├── config.json
├── features.json
├── metrics.json
└── metadata.json
```

---

## Dataset contract

Column prefixes enforce what can be used at each stage:

| Prefix | Usage | Description |
|--------|-------|-------------|
| `feature_*` | Model input X | Known at decision time |
| `target_*` | Label y | Future outcomes — never features |
| `id_*` | Join keys | Dedup only |
| `audit_*` | Debug | Timestamps for human review |

The demo generates a synthetic table in `data/synthetic/ml_demo_table.parquet`.

---

## Temporal validation

Time-series data requires **date-based splits**, not random shuffling.

```
|-------- train --------|-- val --|-- test --|
        older dates                  newer dates
```

Walk-forward backtest (expanding window) is the production pattern for
estimating out-of-sample performance. The demo implements a simple hold-out split.

---

## Deployment integration

The `MLPredictor` class loads any registered version:

```python
from quant_demo.ml.predict import MLPredictor

predictor = MLPredictor(registry_dir="models", version="v001")
should_trade, prob = predictor.should_trade(features_dict, threshold=0.55)
```

In the live runner, this sits **after** feature extraction and **before** the risk engine.

---

## What the demo uses vs production

| Aspect | Demo | Production pattern |
|--------|------|-------------------|
| Algorithm | Logistic regression | LightGBM, ensembles |
| Data | Synthetic random walk | Real feature logs from live/paper |
| Feature selection | Top-N by correlation | Correlation filter + tree importance |
| Backtest | Hold-out metrics | Walk-forward P&L simulation |

The **engineering contract** (config, registry, predictor interface) is the same.

---

## Known pitfalls (documented honestly)

- Small sample sizes → overfitting; aggressive feature selection required.
- Single market regime → poor generalization; extend date range.
- Class imbalance → use `class_weight` or resampling.
- Label leakage → strict `feature_*` / `target_*` separation at schema level.
