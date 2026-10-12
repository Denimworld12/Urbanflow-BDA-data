# UrbanFlow — real data, trained model & gold results (private)

This repo holds the **outputs** of one completed Tier 2 (FHVHV, 243.5M rows) run of
[`Urbanflow-BDA`](https://github.com/Denimworld12/Urbanflow-BDA) — the trained
duration model and the six gold analysis tables — so a teammate can see the
real dashboard without retraining (which took several hours).

It also holds **real bronze and silver data** from that same Tier 2 dataset
(NYC TLC high-volume for-hire trips — Uber/Lyft — 2025), so the data itself can
be browsed directly on GitHub or in a Codespace with no download step.

This repo is **private** on purpose: it's not source code, it's a specific
run's output, and it's kept separate so the public code repo never needs to
touch it.

## What's in here

```
data/raw/        BRONZE: the immutable raw download from the NYC TLC, as published
                 (fhvhv/year=2025/fhvhv_2025-MM.parquet + taxi_zone_lookup.csv + manifest.csv)
data/curated/    SILVER: cleaned, enriched, zone-joined, partitioned by year/month
                 (fhvhv/year=2025/month=M/*.parquet + quality_report.json)
                 + fhvhv_2025-MM_sample.csv: first 50,000 rows of each month, a SAMPLE only
data/gold/       the 6 analysis tables + model_results.json + benchmarks.json
                 + duration_predictions (the Predict tab's precomputed grid)
                 + <table>.csv next to every table: the COMPLETE table as CSV
data/models/     the actual trained Spark ML pipeline (duration_gbt/)
scripts/         export_full_csv.py: writes any table/month out as CSV locally
```

### CSV versions

* **Gold — full CSVs.** Every gold table has a complete CSV copy next to it
  (`data/gold/daily_kpis.csv`, `demand_by_zone_hour.csv`, …, every row, the
  same as the Parquet table). Open them in Excel, pandas, anything.
* **Silver — labelled samples only.** `data/curated/fhvhv_2025-MM_sample.csv`
  holds just the **first 50,000 rows** of that month (out of ~20M), so you can
  look at real clean trips in a spreadsheet. They are **samples, not the full
  month**. A full month as CSV is ~3.7 GB (CSV is ~7x bigger than Parquet), so
  the complete CSVs would push this repo past 20 GB, and they are not committed.
* **Full silver CSV on demand.** Generate the complete CSV for any month locally
  (needs only `pyarrow`; ~15 s and ~3.7 GB per month):
  ```bash
  pip install -r requirements.txt
  python scripts/export_full_csv.py data/curated/fhvhv/year=2025/month=1
  # -> data/curated/fhvhv_2025-01_full.csv   (20,399,680 rows; git-ignored)
  ```
  The same script works on any Parquet file or folder here, e.g. a bronze
  month: `python scripts/export_full_csv.py data/raw/fhvhv/year=2025/fhvhv_2025-01.parquet -o jan_raw.csv`.

| Layer | Path | Contents | Rows | On disk |
|---|---|---|---|---|
| Bronze | `data/raw/` | FHVHV Jan–May 2025, as downloaded | 101,127,182 | 2.43 GB |
| Silver | `data/curated/` | the same 5 months, cleaned + zone-joined (+ 5 sample CSVs, 48 MB) | 101,099,657 | 2.66 GB |
| Gold | `data/gold/` | 6 answer tables + model metrics + benchmarks, from all 12 months (+ full CSVs, 2.4 MB) | 243.5M trips summarised | 2.6 MB |
| Models | `data/models/` | trained duration GBT pipeline, from all 12 months | — | 109 KB |
| **Total** | `data/` | | | **5.09 GB** |

**Which data this is:** Tier 2 of the code repo (`make ingest TIER=2` then
`make curate TIER=2`), dataset `fhvhv`, i.e. 12 months of 2025, ~243.6M raw
rows. The gold tables and the model were built from **all 12 months** of that
run and are unchanged. Bronze and silver here are a **representative 5-month
slice (January–May 2025)** of the same real data, regenerated with the same
code, kept to ~5 GB so a GitHub Codespace clones and opens it reliably. The
full 12 months is ~11.7 GB (bronze 5.6 GB + silver 6.1 GB). Every row count above
is real and can be checked: bronze per month in `data/raw/manifest.csv`, silver
per month (with how many rows each cleaning rule removed) in
`data/curated/quality_report.json`.

**Why bronze months are folders:** GitHub rejects any file over 100 MB, and
each monthly TLC file is ~460–520 MB. So each `fhvhv_2025-MM.parquet` is a
folder of Parquet chunks (`part-000.parquet`, …, each under 90 MB), split
without changing any row, column or type. Spark and pyarrow read such a
folder exactly like the single file, so the code repo's `curate` and
streaming producer work on it unchanged. `manifest.csv` still records the
original file's byte size and row count as downloaded. Silver is Spark's own
output and is already split into parts under 90 MB (Spark's `.crc` checksum
side-files are left out).

## How bronze → silver → gold works

* **Bronze (`data/raw/`) — the raw copy.** `make ingest` downloads each month's
  Parquet file from the NYC TLC website and never edits it. Every download is
  logged in `manifest.csv` (bytes, rows, time). If anything later looks wrong,
  you can always go back to exactly what the city published.
* **Silver (`data/curated/`) — the clean, analysis-ready copy.** `make curate`
  reads bronze with Spark and: renames the columns into one common schema;
  derives duration, speed, pickup hour, weekday and tip %; removes impossible
  trips (e.g. under 1 minute or over 6 hours, over 100 miles, over 90 mph,
  negative fares, timestamps outside the month); joins the 265-row NYC zone
  table on both pickup and dropoff (a broadcast join, so the big table is not
  shuffled) to add borough and zone names; and writes Parquet partitioned by
  year/month so a query for one month only opens that month's folder. Only
  ~0.03% of rows fail the cleaning rules.
* **Gold (`data/gold/`) — the answers.** `make gold` aggregates silver into six
  small tables (demand by zone and hour, daily KPIs, tipping, and so on), and
  `make model` trains the trip-duration model on silver. These are kilobytes,
  not gigabytes, which is why the dashboard loads instantly.

## How to use this — for a new developer

1. Clone or download this repo.
2. Copy its `data/` folder into your local `Urbanflow-BDA/urbanflow-repo/data/`
   — merge, don't replace, if you already have a `data/raw/` or
   `data/curated/` from your own run:
   ```bash
   cp -r data/gold    /path/to/Urbanflow-BDA/urbanflow-repo/data/gold
   cp -r data/models  /path/to/Urbanflow-BDA/urbanflow-repo/data/models
   # optional, only to work with the real bronze/silver too:
   cp -r data/raw     /path/to/Urbanflow-BDA/urbanflow-repo/data/raw
   cp -r data/curated /path/to/Urbanflow-BDA/urbanflow-repo/data/curated
   ```
3. From `urbanflow-repo/`, just run:
   ```bash
   make dash
   # or: docker compose up -d   (the entrypoint already skips retraining
   # once it sees data/gold/benchmarks.json, and starts the dashboard straight away)
   ```

You get the real, already-trained dashboard in seconds — no Spark, no
multi-hour training run.
