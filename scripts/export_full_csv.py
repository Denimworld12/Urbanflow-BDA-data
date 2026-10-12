"""Export a Parquet table (a file, or a Spark output folder) to CSV.

Run it on a silver month to get that month's COMPLETE CSV locally, without it
having to live in git:

    python scripts/export_full_csv.py data/curated/fhvhv/year=2025/month=1
    # -> data/curated/fhvhv_2025-01_full.csv  (~20.4M rows, several GB)

Also used to build the committed CSVs: the full gold tables, and the silver
samples with --limit 50000.

Needs only pyarrow (pip install -r requirements.txt). Streams in batches, so a
20M-row month does not need to fit in memory.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.dataset as ds


def parquet_files(path: Path) -> list[str]:
    if path.is_file():
        return [str(path)]
    # sorted, so "the first N rows" is the same on every machine
    return sorted(str(p) for p in path.rglob("*.parquet")
                  if p.is_file() and not any(part.startswith((".", "_")) for part in p.relative_to(path).parts))


def path_partitions(path: Path) -> dict[str, int]:
    """Spark puts partition columns (year=2025/month=1) in the folder names, not the files."""
    return {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", path.as_posix())}


def default_output(path: Path, limit: int | None) -> Path:
    parts = path_partitions(path)
    if "year" in parts and "month" in parts:
        dataset = path.parents[1].name                      # .../<dataset>/year=Y/month=M
        name = f"{dataset}_{parts['year']:04d}-{parts['month']:02d}"
        return path.parents[2] / f"{name}_{'sample' if limit else 'full'}.csv"
    return path.parent / f"{path.name.removesuffix('.parquet')}.csv"


def export(path: Path, out: Path, limit: int | None = None) -> int:
    files = parquet_files(path)
    if not files:
        raise SystemExit(f"no parquet files under {path}")
    parts = path_partitions(path)
    # a silver month folder (.../year=Y/month=M) carries year and month only in its path
    extra = {k: parts[k] for k in ("year", "month")} if {"year", "month"} <= parts.keys() else {}
    dataset = ds.dataset(files, format="parquet")
    rows, writer = 0, None
    try:
        for batch in dataset.to_batches():
            if limit is not None:
                if rows >= limit:
                    break
                batch = batch.slice(0, limit - rows)
            for k, v in extra.items():
                if k not in batch.schema.names:
                    batch = batch.append_column(k, pa.array([v] * batch.num_rows, pa.int32()))
            if writer is None:
                writer = pacsv.CSVWriter(str(out), batch.schema)
            writer.write_batch(batch)
            rows += batch.num_rows
    finally:
        if writer is not None:
            writer.close()
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Export a Parquet table or Spark output folder to CSV")
    ap.add_argument("path", type=Path, help="parquet file or folder, e.g. data/curated/fhvhv/year=2025/month=1")
    ap.add_argument("-o", "--out", type=Path, help="output CSV (default: next to the input)")
    ap.add_argument("--limit", type=int, help="write only the first N rows (a SAMPLE, not the full table)")
    a = ap.parse_args()
    out = a.out or default_output(a.path, a.limit)
    n = export(a.path, out, a.limit)
    print(f"{out}  {n:,} rows  {out.stat().st_size / 1e6:.1f} MB")
