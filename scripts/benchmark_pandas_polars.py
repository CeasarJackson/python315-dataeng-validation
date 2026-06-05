"""
================================================================================
benchmark_pandas_polars.py — Benchmark: Pandas vs. Polars
================================================================================
Project  : Python 3.15 Data Engineering Validation Suite
Author   : Dr. Ceasar Jackson Jr.
Platform : macOS 26.5 ARM64
Manager  : uv
================================================================================

PURPOSE
-------
Measures and compares execution time for equivalent analytical operations
performed in Pandas and Polars across three dataset sizes.  Results are logged
to the terminal (colored) and saved as a CSV to data/benchmark_pandas_polars.csv
for archiving and later visualization.

BENCHMARK OPERATIONS
--------------------
  1. DataFrame creation from Python lists
  2. Filter  — select rows matching a condition
  3. GroupBy — aggregate sum and mean by a categorical column
  4. Sort    — order by a numeric column, descending
  5. Join    — inner join of two tables on a key column

DATASET SIZES
-------------
  Small  :   100,000 rows
  Medium : 1,000,000 rows
  Large  : 5,000,000 rows

Note: "Large" may take 30–60 seconds on first run depending on available
memory.  Reduce SIZES below if memory is constrained.

OUTPUT
------
  Terminal : Colored timing table via logger
  CSV      : data/benchmark_pandas_polars.csv
             Columns: size, operation, pandas_s, polars_s, speedup_x

INTERPRETATION
--------------
  speedup_x > 1.0  → Polars is faster than Pandas for that operation/size
  speedup_x < 1.0  → Pandas is faster (rare, usually small-dataset overhead)

USAGE
-----
  python scripts/benchmark_pandas_polars.py

NOTES
-----
  - Each benchmark is run RUNS=3 times; the median is reported to reduce
    noise from JIT warm-up (Polars) and GC pauses (both).
  - Polars LazyFrame API is used where applicable for a fair comparison
    against Pandas' standard eager API.
  - Results depend heavily on available RAM and CPU cores.  Record the
    hardware spec alongside benchmark results for reproducibility.
================================================================================
"""

from __future__ import annotations

import csv
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Bootstrap path
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SIZES: list[int] = [100_000, 1_000_000, 5_000_000]
RUNS: int = 3  # Median over this many runs per operation

CATEGORIES = ["alpha", "beta", "gamma", "delta", "epsilon"]
OUTPUT_CSV = Path(__file__).resolve().parent.parent / "data" / "benchmark_pandas_polars.csv"


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_data(n: int) -> dict[str, list]:
    """Generate a reproducible synthetic dataset of n rows."""
    rng = random.Random(42)
    return {
        "id":       list(range(n)),
        "category": [rng.choice(CATEGORIES) for _ in range(n)],
        "value_a":  [rng.uniform(0, 1000) for _ in range(n)],
        "value_b":  [rng.uniform(0, 500)  for _ in range(n)],
        "join_key": [rng.randint(0, n // 10) for _ in range(n)],
    }


def generate_lookup(n: int) -> dict[str, list]:
    """Generate a small lookup table for join benchmarks."""
    keys = list(range(n // 10 + 1))
    return {
        "join_key": keys,
        "label":    [f"label_{k}" for k in keys],
    }


# ---------------------------------------------------------------------------
# Timer helper
# ---------------------------------------------------------------------------

def timed(fn: Callable, runs: int = RUNS) -> float:
    """Run *fn* *runs* times and return the median elapsed time in seconds."""
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


# ---------------------------------------------------------------------------
# Pandas benchmarks
# ---------------------------------------------------------------------------

def bench_pandas(data: dict, lookup: dict) -> dict[str, float]:
    """Run all operations in Pandas and return timing dict."""
    import pandas as pd  # noqa: PLC0415

    results: dict[str, float] = {}

    # 1. Creation
    def create():
        return pd.DataFrame(data)

    results["creation"] = timed(create)
    df = pd.DataFrame(data)
    ldf = pd.DataFrame(lookup)

    # 2. Filter
    results["filter"] = timed(lambda: df[df["value_a"] > 500.0])

    # 3. GroupBy
    results["groupby"] = timed(
        lambda: df.groupby("category").agg(
            sum_a=("value_a", "sum"),
            mean_b=("value_b", "mean"),
        ).reset_index()
    )

    # 4. Sort
    results["sort"] = timed(lambda: df.sort_values("value_a", ascending=False))

    # 5. Join
    results["join"] = timed(lambda: df.merge(ldf, on="join_key", how="inner"))

    return results


# ---------------------------------------------------------------------------
# Polars benchmarks
# ---------------------------------------------------------------------------

def bench_polars(data: dict, lookup: dict) -> dict[str, float]:
    """Run all operations in Polars (LazyFrame where applicable) and return timing dict."""
    import polars as pl  # noqa: PLC0415

    results: dict[str, float] = {}

    # 1. Creation
    def create():
        return pl.DataFrame(data)

    results["creation"] = timed(create)
    df = pl.DataFrame(data)
    ldf = pl.DataFrame(lookup)

    # 2. Filter (LazyFrame)
    results["filter"] = timed(
        lambda: df.lazy().filter(pl.col("value_a") > 500.0).collect()
    )

    # 3. GroupBy (LazyFrame)
    results["groupby"] = timed(
        lambda: df.lazy().group_by("category").agg(
            pl.col("value_a").sum().alias("sum_a"),
            pl.col("value_b").mean().alias("mean_b"),
        ).collect()
    )

    # 4. Sort (LazyFrame)
    results["sort"] = timed(
        lambda: df.lazy().sort("value_a", descending=True).collect()
    )

    # 5. Join (LazyFrame)
    results["join"] = timed(
        lambda: df.lazy().join(ldf.lazy(), on="join_key", how="inner").collect()
    )

    return results


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> int:
    log.info("=" * 70)
    log.info("Benchmark — Pandas vs. Polars")
    log.info("Author  : Dr. Ceasar Jackson Jr.")
    log.info("Python  : %s", sys.version.split()[0])
    log.info("Runs    : %d (median reported)", RUNS)
    log.info("=" * 70)

    try:
        import pandas as pd  # noqa: PLC0415, F401
        import polars as pl  # noqa: PLC0415, F401
    except ImportError as exc:
        log.error("Required packages not installed: %s", exc)
        return 1

    all_rows: list[dict] = []

    for size in SIZES:
        log.info("-" * 70)
        log.info("Dataset size: %s rows", f"{size:,}")
        log.info("Generating data...")
        data = generate_data(size)
        lookup = generate_lookup(size)

        log.info("Running Pandas benchmarks...")
        pd_times = bench_pandas(data, lookup)

        log.info("Running Polars benchmarks...")
        pl_times = bench_polars(data, lookup)

        log.info("")
        log.info(
            "  %-12s  %10s  %10s  %10s",
            "Operation", "Pandas (s)", "Polars (s)", "Speedup"
        )
        log.info("  " + "-" * 48)

        for op in pd_times:
            pd_t = pd_times[op]
            pl_t = pl_times[op]
            speedup = pd_t / pl_t if pl_t > 0 else float("inf")

            if speedup >= 1.5:
                log.info("  %-12s  %10.4f  %10.4f  %8.2fx  ← Polars faster", op, pd_t, pl_t, speedup)
            elif speedup <= 0.7:
                log.warning("  %-12s  %10.4f  %10.4f  %8.2fx  ← Pandas faster", op, pd_t, pl_t, speedup)
            else:
                log.info("  %-12s  %10.4f  %10.4f  %8.2fx", op, pd_t, pl_t, speedup)

            all_rows.append({
                "size":       size,
                "operation":  op,
                "pandas_s":   round(pd_t, 6),
                "polars_s":   round(pl_t, 6),
                "speedup_x":  round(speedup, 3),
            })

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["size", "operation", "pandas_s", "polars_s", "speedup_x"])
        writer.writeheader()
        writer.writerows(all_rows)

    log.info("=" * 70)
    log.info("Benchmark complete.  Results saved to: %s", OUTPUT_CSV)
    return 0


if __name__ == "__main__":
    sys.exit(main())
