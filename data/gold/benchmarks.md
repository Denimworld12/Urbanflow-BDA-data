# Benchmark results

_Measure on your own machine and quote these numbers in the report._

## scale

- **rows**: 243506519
- **month_partitions**: 12

> Context for every timing below. Benchmarks on small data measure overhead, not throughput.

## format

- **parquet_s**: 5.119
- **csv_s**: 293.016
- **speedup**: 57.24

> Parquet reads only the columns the query touches; CSV must decode every byte of every row.

## partitioning

- **partitioned_s**: 0.278
- **flat_s**: 0.677
- **speedup**: 2.44
- **queried**: 2025-11

> Partition pruning lets Spark skip whole folders using the directory names, before opening any file.

## join

- **broadcast_s**: 1.218
- **sort_merge_s**: 17.704
- **speedup**: 14.54

> Broadcasting the 265-row zone table avoids shuffling 240M trip rows across partitions. Run .explain() on both to show BroadcastHashJoin vs SortMergeJoin.

## cores

- **seconds**: {'1': 7.514, '2': 4.367, '4': 1.985}
- **speedup_vs_1**: {'1': 1.0, '2': 1.72, '4': 3.79}

> Speedup is sub-linear: coordination overhead, shuffle writes and a single shared disk mean N cores never give N times the throughput. Amdahl's law in one chart.
