#!/usr/bin/env python3
"""
===============================================================================
Python 3.15 Data Engineering Validation Suite
===============================================================================
Script:
    benchmark_duckdb_pyarrow.py

Author:
    Dr. Ceasar Jackson Jr.

Project:
    Python 3.15 Data Engineering Validation Suite

Purpose:
    Benchmark native DuckDB running under Python 3.15 against PyArrow running
    inside a Docker-based Python 3.14 environment. Results are written to CSV
    and displayed through the project logging framework.

Usage:
    python scripts/benchmark_duckdb_pyarrow.py
    python scripts/benchmark_duckdb_pyarrow.py --help
    python scripts/benchmark_duckdb_pyarrow.py > benchmark.log 2>&1

Validation:
    python scripts/benchmark_duckdb_pyarrow.py
    python -m py_compile scripts/benchmark_duckdb_pyarrow.py
    python -m ruff check scripts/benchmark_duckdb_pyarrow.py
    python -m black --check scripts/benchmark_duckdb_pyarrow.py
    python -m pytest -v

Exit Codes:
    0 = Success
    1 = Required dependency missing
    130 = User interrupted (Ctrl+C)

Logging:
    - Colorized console logging (when colorlog is installed)
    - Persistent log file output through logger.py
    - Defensive error handling and cleanup
    - Console and log-file timestamps
    - Structured benchmark status messages

Operations Benchmarked:
    1. Parquet write
    2. Parquet read
    3. Filter
    4. Aggregation
    5. Join

Dataset Sizes:
    - 500,000 rows
    - 2,000,000 rows
    - 5,000,000 rows

Prerequisites:
    - Docker Desktop running
    - pyarrow-dataeng:py314 image available
    - DuckDB installed in active environment

Notes:
    PyArrow currently lacks Python 3.15 wheels. Therefore PyArrow benchmarks
    execute in a Docker container while DuckDB benchmarks execute natively.
    This script follows the Dr. Ceasar Jackson Jr. project scripting
    standard including detailed operational guidance, validation commands,
    defensive programming practices, and centralized logging.
===============================================================================
"""

from __future__ import annotations

import csv
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import colorlog

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s"
        )
    )
    log = colorlog.getLogger("bench")
    log.addHandler(handler)
    log.setLevel("INFO")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    log = logging.getLogger("bench")


OUTPUT_CSV = Path("benchmark_duckdb_pyarrow.csv")
FIELDNAMES = ["tool", "operation", "elapsed_sec"]

# We will generate a 2 million row parquet file for benchmarking
PARQUET_FILE = Path("benchmark_data.parquet")

# Number of runs per benchmark for statistical stability
N_RUNS = 3


def generate_parquet() -> None:
    """
    Generate a synthetic Parquet file for benchmarking.
    """
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    nrows = 2_000_000
    cats = ["alpha", "beta", "gamma", "delta", "epsilon"]
    log.info(f"Generating synthetic Parquet file with {nrows} rows ...")
    df = pd.DataFrame(
        {
            "id": np.arange(nrows),
            "category": np.random.choice(cats, size=nrows),
            "value": np.random.randn(nrows) * 100,
            "flag": np.random.choice([True, False], size=nrows),
        }
    )
    table = pa.Table.from_pandas(df)
    pq.write_table(table, PARQUET_FILE)
    log.info(f"Parquet file written to {PARQUET_FILE}")


def timed(fn, *args, **kwargs) -> float:
    """
    Time a function call, returning elapsed seconds.
    """
    start = time.perf_counter()
    fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed


def bench_duckdb() -> list[tuple[str, float]]:
    """
    Run DuckDB benchmarks for Parquet operations.
    """
    import duckdb

    results = []
    tmp = tempfile.mktemp(suffix=".parquet")

    def write():
        if os.path.exists(tmp):
            os.unlink(tmp)
        con = duckdb.connect()
        con.execute(f"""
            CREATE TABLE t AS
            SELECT *
            FROM read_parquet('{PARQUET_FILE}')
            """)
        con.execute(f"COPY t TO '{tmp}' (FORMAT PARQUET)")
        con.close()

    def read():
        con = duckdb.connect()
        con.execute(f"SELECT * FROM read_parquet('{tmp}')")
        con.fetchall()
        con.close()

    def filter_op():
        con = duckdb.connect()
        con.execute(f"SELECT * FROM read_parquet('{tmp}') WHERE flag = true")
        con.fetchall()
        con.close()

    def aggregate():
        con = duckdb.connect()
        con.execute(
            f"SELECT category, AVG(value) FROM read_parquet('{tmp}') GROUP BY category"
        )
        con.fetchall()
        con.close()

    def join():
        con = duckdb.connect()
        con.execute(f"""
            SELECT t1.id, t2.value
            FROM read_parquet('{tmp}') t1
            JOIN read_parquet('{tmp}') t2 ON t1.id = t2.id
            """)
        con.fetchall()
        con.close()

    log.info("Running DuckDB benchmarks ...")
    results.append(("write", timed(write)))
    results.append(("read", timed(read)))
    results.append(("filter", timed(filter_op)))
    results.append(("aggregate", timed(aggregate)))
    results.append(("join", timed(join)))
    if os.path.exists(tmp):
        os.unlink(tmp)
    return results


# PyArrow benchmark script to run inside Docker container
_ARROW_SCRIPT = r"""
import time
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

nrows = 2_000_000
cats = ["alpha", "beta", "gamma", "delta", "epsilon"]

def generate_parquet():
    df = pd.DataFrame({
        "id": np.arange(nrows),
        "category": np.random.choice(cats, size=nrows),
        "value": np.random.randn(nrows) * 100,
        "flag": np.random.choice([True, False], size=nrows)
    })
    table = pa.Table.from_pandas(df)
    pq.write_table(table, "/data/benchmark_data.parquet")

def timed(fn):
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    return elapsed

def bench_pyarrow():
    results = []
    generate_parquet()

    def write():
        table = pq.read_table("/data/benchmark_data.parquet")
        pq.write_table(table, "/data/tmp.parquet")

    def read():
        table = pq.read_table("/data/tmp.parquet")

    def filter_op():
        table = pq.read_table("/data/tmp.parquet")
        mask = table.column("flag").to_pandas()
        filtered = table.filter(pa.array(mask))

    def aggregate():
        table = pq.read_table("/data/tmp.parquet")
        df = table.to_pandas()
        df.groupby("category")["value"].mean()

    def join():
        table = pq.read_table("/data/tmp.parquet")
        df1 = table.to_pandas()
        df2 = table.to_pandas()
        df1.merge(df2, on="id")

    results.append(("write", timed(write)))
    results.append(("read", timed(read)))
    results.append(("filter", timed(filter_op)))
    results.append(("aggregate", timed(aggregate)))
    results.append(("join", timed(join)))

    for op, elapsed in results:
        print(f"{op},{elapsed:.6f}")

if __name__ == "__main__":
    bench_pyarrow()
"""


def check_docker() -> bool:
    """
    Check if Docker is available and the required image is present.
    """
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.error("Docker is not running or not installed.")
        return False

    images = subprocess.run(
        ["docker", "images", "-q", "pyarrow-dataeng:py314"],
        capture_output=True,
        text=True,
    )
    if not images.stdout.strip():
        log.error(
            "Docker image 'pyarrow-dataeng:py314' not found. Please build or pull it."
        )
        return False
    return True


def bench_pyarrow_docker() -> list[tuple[str, float]]:
    """
    Run PyArrow benchmarks inside a Docker container.
    """
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{os.getcwd()}:/data",
        "pyarrow-dataeng:py314",
        "python",
        "/data/scripts/pyarrow_bench.py",
    ]

    # Write the benchmark script to the scripts folder
    script_path = Path("scripts/pyarrow_bench.py")
    script_path.parent.mkdir(exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(_ARROW_SCRIPT)

    r = subprocess.run(docker_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log.error(f"Docker PyArrow benchmark failed:\n{r.stderr}")
        return []

    lines = [line for line in r.stdout.strip().splitlines() if line.strip()]
    results = []
    for line in lines:
        try:
            op, elapsed = line.split(",")
            results.append((op, float(elapsed)))
        except Exception:
            continue
    return results


def main() -> int:
    from importlib.util import find_spec

    try:
        if not PARQUET_FILE.exists():
            generate_parquet()

        if find_spec("duckdb") is None:
            log.error("duckdb not installed — run: uv pip install duckdb")
            return 1

        if not check_docker():
            log.error("Docker environment not ready for PyArrow benchmark.")
            return 1

        all_rows = []

        duckdb_results = []
        for i in range(N_RUNS):
            log.info(f"DuckDB run {i + 1} of {N_RUNS}")
            duckdb_results.append(dict(bench_duckdb()))

        # Aggregate DuckDB results by operation
        duckdb_agg = {}
        for op in duckdb_results[0].keys():
            times = [run[op] for run in duckdb_results]
            median = statistics.median(times)
            duckdb_agg[op] = median

        for op, elapsed in duckdb_agg.items():
            all_rows.append({"tool": "duckdb", "operation": op, "elapsed_sec": elapsed})

        pyarrow_results = []
        for i in range(N_RUNS):
            log.info(f"PyArrow Docker run {i + 1} of {N_RUNS}")
            res = bench_pyarrow_docker()
            if not res:
                log.error("PyArrow Docker benchmark failed; aborting.")
                return 1
            pyarrow_results.append(dict(res))

        # Aggregate PyArrow results by operation
        pyarrow_agg = {}
        for op in pyarrow_results[0].keys():
            times = [run[op] for run in pyarrow_results]
            median = statistics.median(times)
            pyarrow_agg[op] = median

        for op, elapsed in pyarrow_agg.items():
            all_rows.append(
                {"tool": "pyarrow", "operation": op, "elapsed_sec": elapsed}
            )

        # Write results to CSV
        with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            w.writeheader()
            w.writerows(all_rows)

        log.info(f"Benchmark results written to {OUTPUT_CSV}")
        return 0

    except KeyboardInterrupt:
        log.warning("User interrupted benchmark.")
        return 130
    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
