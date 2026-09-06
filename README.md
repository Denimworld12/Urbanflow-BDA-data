# UrbanFlow — trained model & gold results (private)

This repo holds the **outputs** of one completed Tier 2 (FHVHV, 243.5M rows) run of
[`Urbanflow-BDA`](https://github.com/Denimworld12/Urbanflow-BDA) — the trained
duration model and the six gold analysis tables — so a teammate can see the
real dashboard without retraining (which took several hours).

This repo is **private** on purpose: it's not source code, it's a specific
run's output, and it's kept separate so the public code repo never needs to
touch it.

## What's in here

```
data/gold/       the 6 analysis tables + model_results.json + benchmarks.json
                 + duration_predictions (the Predict tab's precomputed grid)
data/models/     the actual trained Spark ML pipeline (duration_gbt/)
```

## How to use this — for a new developer

1. Clone or download this repo.
2. Copy its `data/` folder into your local `Urbanflow-BDA/urbanflow-repo/data/`
   — merge, don't replace, if you already have a `data/raw/` or
   `data/curated/` from your own run:
   ```bash
   cp -r data/gold    /path/to/Urbanflow-BDA/urbanflow-repo/data/gold
   cp -r data/models  /path/to/Urbanflow-BDA/urbanflow-repo/data/models
   ```
3. From `urbanflow-repo/`, just run:
   ```bash
   make dash
   # or: docker compose up -d   (the entrypoint already skips retraining
   # once it sees data/gold/benchmarks.json, and starts the dashboard straight away)
   ```

You get the real, already-trained dashboard in seconds — no Spark, no
multi-hour training run.
