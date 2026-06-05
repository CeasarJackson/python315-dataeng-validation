"""
================================================================================
benchmark_duckdb_pyarrow.py — Phase 7 Benchmark: DuckDB vs. PyArrow
================================================================================
Project  : Python 3.15 Data Engineering Validation Suite
Author   : Dr. Ceasar Jackson Jr.
Platform : macOS 26.5 ARM64 · Python 3.15.0b1 (host) / Python 3.14 (Docker)
Manager  : uv
================================================================================

PURPOSE
-------
Benchmarks DuckDB (running natively on Python 3.15) against PyArrow (running
inside the pyarrow-dataeng:py314 Docker container) for five core operations:

  1. Parquet write  — serialize a synthetic dataset to Parquet
  2. Parquet read   — deserialize from Parquet to in-memory table
  3. Filter         — select rows matching a predicate
  4. Aggregation    — groupby + sum + mean
  5. Join           — inner join two tables on a key column

ARCHITECTURE
------------
PyArrow cannot be installed in Python 3.15 (no cp315 wheels), so its
benchmarks run inside the pyarrow-dataeng:py314 Docker container.
DuckDB generates Parquet files in a shared temp directory that is
mounted into the container read-only at /benchmark_data.

  Python 3.15 host  →  generates Parquet via DuckDB
                    →  runs DuckDB benchmarks
                    →  pipes benchmark script into Docker container
  Docker py314      →  runs PyArrow benchmarks on same Parquet files
                    →  returns JSON results to host

DATASET SIZES
-------------
  Small  :   500,000 rows
  Medium : 2,000,000 rows
  Large  : 5,000,000 rows

RUNS
----
  Median of 3 runs per operation/size.

OUTPUT
------
  Terminal : Colored timing table via logger
  CSV      : data/benchmark_duckdb_pyarrow.csv
             Columns: size, operation, duckdb_s, pyarrow_s, winner, speedup_x

PREREQUISITES
-------------
  - Docker Desktop running
  - pyarrow-dataeng:py314 image built:
      cd docker_pyarrow_lab && docker build -t pyarrow-dataeng:py314 .
  - Script degrades gracefully if Docker is unavailable (DuckDB only).
================================================================================
"""

from __future__ import annotations

import csv, json, os, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger import get_logger

log = get_logger(__name__)

SIZES       = [500_000, 2_000_000, 5_000_000]
RUNS        = 3
DOCKER_IMAGE = "pyarrow-dataeng:py314"
OUTPUT_CSV  = Path(__file__).resolve().parent.parent / "data" / "benchmark_duckdb_pyarrow.csv"

# ---------------------------------------------------------------------------
# Parquet generation via DuckDB
# ---------------------------------------------------------------------------

def generate_parquet(tmp_dir: str, n: int) -> tuple[str, str]:
    """Generate main + lookup Parquet files using DuckDB SQL."""
    import duckdb
    main_path   = os.path.join(tmp_dir, f"main_{n}.parquet")
    lookup_path = os.path.join(tmp_dir, f"lookup_{n}.parquet")
    cats        = ["alpha","beta","gamma","delta","epsilon"]
    con = duckdb.connect(":memory:")
    con.execute(f"""
        COPY (
            SELECT range AS id,
                   ['alpha','beta','gamma','delta','epsilon'][1 + (range % 5)] AS category,
                   random() * 1000 AS value_a,
                   random() * 500  AS value_b,
                   (range % {max(1, n//10)})::INTEGER AS join_key
            FROM range({n})
        ) TO '{main_path}' (FORMAT PARQUET)
    """)
    con.execute(f"""
        COPY (
            SELECT range AS join_key,
                   'label_' || range::VARCHAR AS label
            FROM range({n//10 + 1})
        ) TO '{lookup_path}' (FORMAT PARQUET)
    """)
    con.close()
    log.debug("Parquet written: %s (%.1f MB)", main_path, os.path.getsize(main_path)/1_048_576)
    return main_path, lookup_path

# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------

def timed(fn, runs=RUNS) -> float:
    times = []
    for _ in range(runs):
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return statistics.median(times)

# ---------------------------------------------------------------------------
# DuckDB benchmarks (Python 3.15 native)
# ---------------------------------------------------------------------------

def bench_duckdb(main_path: str, lookup_path: str) -> dict[str, float]:
    import duckdb
    results = {}
    tmp = tempfile.mktemp(suffix=".parquet")
    con = duckdb.connect(":memory:")
    con.execute(f"CREATE TABLE main   AS SELECT * FROM read_parquet('{main_path}')")
    con.execute(f"CREATE TABLE lookup AS SELECT * FROM read_parquet('{lookup_path}')")

    def write():
        con.execute(f"COPY main TO '{tmp}' (FORMAT PARQUET)")
        if os.path.exists(tmp): os.unlink(tmp)

    results["parquet_write"] = timed(write)
    results["parquet_read"]  = timed(lambda: duckdb.connect(":memory:").execute(
        f"SELECT COUNT(*) FROM read_parquet('{main_path}')").fetchone())
    results["filter"]        = timed(lambda: con.execute(
        "SELECT * FROM main WHERE value_a > 500.0").fetchall())
    results["aggregation"]   = timed(lambda: con.execute(
        "SELECT category, SUM(value_a), AVG(value_b) FROM main GROUP BY category").fetchall())
    results["join"]          = timed(lambda: con.execute(
        "SELECT m.*, l.label FROM main m INNER JOIN lookup l ON m.join_key = l.join_key").fetchall())
    con.close()
    return results

# ---------------------------------------------------------------------------
# PyArrow benchmark script — injected into Docker container via stdin
# ---------------------------------------------------------------------------

_ARROW_SCRIPT = r"""
import json, os, statistics, tempfile, time
try:
    import pyarrow.parquet as pq
    import pyarrow.compute as pc

    main_path   = os.environ["BENCH_MAIN"]
    lookup_path = os.environ["BENCH_LOOKUP"]
    runs        = int(os.environ.get("BENCH_RUNS", "3"))
    tmp         = tempfile.mktemp(suffix=".parquet")

    def timed(fn):
        times = []
        for _ in range(runs):
            t = time.perf_counter(); fn()
            times.append(time.perf_counter() - t)
        return statistics.median(times)

    main_tbl   = pq.read_table(main_path)
    lookup_tbl = pq.read_table(lookup_path)

    def write():
        pq.write_table(main_tbl, tmp)
        if os.path.exists(tmp): os.unlink(tmp)

    results = {}
    results["parquet_write"] = timed(write)
    results["parquet_read"]  = timed(lambda: pq.read_table(main_path))
    results["filter"]        = timed(lambda: main_tbl.filter(pc.greater(main_tbl["value_a"], 500.0)))
    results["aggregation"]   = timed(lambda: main_tbl.group_by("category").aggregate([
        ("value_a","sum"), ("value_b","mean")]))
    # Cast join_key to int64 on both sides to match DuckDB Parquet output type
    import pyarrow as pa
    def _cast_key(tbl):
        idx = tbl.schema.get_field_index("join_key")
        return tbl.set_column(idx, "join_key", tbl["join_key"].cast(pa.int64()))
    main_j   = _cast_key(main_tbl)
    lookup_j = _cast_key(lookup_tbl)
    results["join"] = timed(lambda: main_j.join(lookup_j, "join_key", join_type="inner"))

    print(json.dumps({"results": results, "error": None}))
except Exception as exc:
    print(json.dumps({"results": {}, "error": str(exc)}))
"""

# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

def check_docker() -> bool:
    try:
        r = subprocess.run(["docker","image","inspect",DOCKER_IMAGE],
                           capture_output=True, timeout=10)
        if r.returncode == 0:
            log.info("[OK] Docker image %s found", DOCKER_IMAGE)
            return True
        log.warning("[SKIP] Image %s not found — build with: "
                    "cd docker_pyarrow_lab && docker build -t %s .", DOCKER_IMAGE, DOCKER_IMAGE)
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.warning("[SKIP] Docker unavailable: %s", exc)
        return False


def bench_pyarrow_docker(main_path: str, lookup_path: str, tmp_dir: str) -> Optional[dict]:
    main_rel   = os.path.relpath(main_path,   tmp_dir)
    lookup_rel = os.path.relpath(lookup_path, tmp_dir)
    cmd = [
        "docker","run","--rm","--interactive",
        "-v", f"{tmp_dir}:/benchmark_data:ro",
        "-e", f"BENCH_MAIN=/benchmark_data/{main_rel}",
        "-e", f"BENCH_LOOKUP=/benchmark_data/{lookup_rel}",
        "-e", f"BENCH_RUNS={RUNS}",
        DOCKER_IMAGE, "python3", "-",
    ]
    try:
        r = subprocess.run(cmd, input=_ARROW_SCRIPT, capture_output=True,
                           text=True, timeout=300)
        if r.returncode != 0:
            log.error("Docker exit %d: %s", r.returncode, r.stderr[:400])
            return None
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        if not lines:
            log.error("Docker produced no output. stderr: %s", r.stderr[:400])
            return None
        payload = json.loads(lines[-1])
        if payload.get("error"):
            log.error("PyArrow error in container: %s", payload["error"])
            return None
        return payload["results"]
    except subprocess.TimeoutExpired:
        log.error("Docker timed out after 300s")
        return None
    except json.JSONDecodeError as exc:
        log.error("JSON parse failed: %s", exc)
        return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    log.info("=" * 70)
    log.info("Phase 7 — DuckDB (Python 3.15) vs. PyArrow (Docker py314)")
    log.info("Author  : Dr. Ceasar Jackson Jr.")
    log.info("Python  : %s", sys.version.split()[0])
    log.info("Runs    : %d (median)", RUNS)
    log.info("Image   : %s", DOCKER_IMAGE)
    log.info("=" * 70)

    try:
        import duckdb
    except ImportError:
        log.error("duckdb not installed — run: uv pip install duckdb")
        return 1

    docker_ok = check_docker()
    if not docker_ok:
        log.warning("PyArrow column will show [SKIP] — DuckDB timings still recorded.")

    all_rows = []
    tmp_dir  = tempfile.mkdtemp(prefix="py315_bench_dpa_")
    log.info("Temp dir: %s", tmp_dir)

    try:
        for size in SIZES:
            log.info("-" * 70)
            log.info("Dataset: %s rows", f"{size:,}")

            log.info("Generating Parquet via DuckDB...")
            main_path, lookup_path = generate_parquet(tmp_dir, size)
            log.info("Main file: %.1f MB", os.path.getsize(main_path)/1_048_576)

            log.info("Running DuckDB benchmarks (Python 3.15)...")
            duck = bench_duckdb(main_path, lookup_path)

            arrow = None
            if docker_ok:
                log.info("Running PyArrow benchmarks (Docker %s)...", DOCKER_IMAGE)
                arrow = bench_pyarrow_docker(main_path, lookup_path, tmp_dir)
                if arrow is None:
                    log.warning("PyArrow Docker run failed — skipping for this size.")

            log.info("")
            log.info("  %-16s  %10s  %12s  %10s", "Operation","DuckDB (s)","PyArrow (s)","Winner")
            log.info("  " + "-" * 52)

            for op in ["parquet_write","parquet_read","filter","aggregation","join"]:
                dt = duck.get(op, 0.0)
                if arrow and op in arrow:
                    at = arrow[op]
                    if dt <= at:
                        winner, speedup = "DuckDB",  at/dt  if dt  > 0 else float("inf")
                        log.info("  %-16s  %10.4f  %12.4f  %s (%.2fx faster)", op, dt, at, winner, speedup)
                    else:
                        winner, speedup = "PyArrow", dt/at  if at  > 0 else float("inf")
                        log.info("  %-16s  %10.4f  %12.4f  %s (%.2fx faster)", op, dt, at, winner, speedup)
                    all_rows.append({"size":size,"operation":op,"duckdb_s":round(dt,6),
                                     "pyarrow_s":round(at,6),"winner":winner,"speedup_x":round(speedup,3)})
                else:
                    log.info("  %-16s  %10.4f  %12s", op, dt, "[SKIP]")
                    all_rows.append({"size":size,"operation":op,"duckdb_s":round(dt,6),
                                     "pyarrow_s":None,"winner":"DuckDB (only)","speedup_x":None})
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        log.debug("Cleaned up %s", tmp_dir)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["size","operation","duckdb_s","pyarrow_s","winner","speedup_x"])
        w.writeheader(); w.writerows(all_rows)

    log.info("=" * 70)
    log.info("Complete. CSV: %s", OUTPUT_CSV)
    duck_w  = sum(1 for r in all_rows if r["winner"] == "DuckDB")
    arrow_w = sum(1 for r in all_rows if r["winner"] == "PyArrow")
    if duck_w + arrow_w > 0:
        log.info("Overall — DuckDB wins: %d  PyArrow wins: %d", duck_w, arrow_w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
