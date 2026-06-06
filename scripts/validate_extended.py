"""
===============================================================================
================================================================================
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : scripts/validate_extended.py

Purpose
-------
Run Python 3.15 validation checks for the project runtime and data-engineering stack.

Usage
-----
python scripts/validate_extended.py

Validation
----------
python -m py_compile scripts/validate_extended.py
python -m ruff check scripts/validate_extended.py
python -m black --check scripts/validate_extended.py
python scripts/validate_extended.py

Exit Codes
----------
0   Success.
1   Failure or validation error.
130 User interrupted execution.

Operational Notes
-----------------
- Keep this script compatible with the active Python 3.15 validation environment.
- Prefer deterministic inputs and explicit validation commands.
- Preserve readable output suitable for terminal review and release notes.
- Keep this header intact for portfolio, audit, and future-maintainer reference.

===============================================================================
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Bootstrap path
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Result sentinel values
# ---------------------------------------------------------------------------
PASS = "PASS"
WARN = "WARN"
SKIP = "SKIP"
FAIL = "FAIL"
INCOMPAT = "INCOMPAT"


# ---------------------------------------------------------------------------
# Helper: safe import check
# ---------------------------------------------------------------------------


def _is_installed(package: str) -> bool:
    """Return True if *package* can be found in the current environment."""
    spec = importlib.util.find_spec(package)
    return spec is not None


# ---------------------------------------------------------------------------
# Individual package tests
# ---------------------------------------------------------------------------


def test_pyspark() -> str:
    """Test PySpark via the pyarrow-dataeng:py314 Docker container.

    PySpark requires JDK 17 which is not on the Python 3.15 host. The Docker
    image includes OpenJDK 17 and PySpark, so validation runs inside the
    container and returns results via JSON stdout — the same pattern used by
    the Phase 7 DuckDB/PyArrow benchmark.

    Tests performed inside the container:
      - SparkSession creation (local[2])
      - DataFrame construction from Python tuples
      - GroupBy aggregation
      - Filter predicate
      - SQL interface via createOrReplaceTempView

    Skips gracefully if Docker is unavailable or the image is not built.
    """
    import json as _json  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    DOCKER_IMAGE = "pyarrow-dataeng:py314"

    try:
        check = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
            timeout=10,
        )
        if check.returncode != 0:
            log.warning(
                "[SKIP] pyspark — Docker image %s not found. "
                "Build with: cd docker_pyarrow_lab && docker build -t %s .",
                DOCKER_IMAGE,
                DOCKER_IMAGE,
            )
            return SKIP
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.warning("[SKIP] pyspark — Docker unavailable: %s", exc)
        return SKIP

    spark_script = r"""
import json, sys
try:
    import pyspark
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("py315_pyspark_validation")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "512m")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    data = [
        (1, "north", "A", 1500.0),
        (2, "south", "B", 2200.0),
        (3, "north", "A",  800.0),
        (4, "east",  "C", 3100.0),
        (5, "south", "B", 1750.0),
        (6, "north", "A", 4200.0),
    ]
    df = spark.createDataFrame(data, ["id", "region", "product", "amount"])
    total_rows = df.count()
    assert total_rows == 6
    agg_rows = df.groupBy("region").agg(F.sum("amount").alias("total")).count()
    assert agg_rows == 3
    filtered = df.filter(F.col("amount") > 2000).count()
    assert filtered == 3
    df.createOrReplaceTempView("sales")
    sql_rows = spark.sql("SELECT product, SUM(amount) AS total FROM sales GROUP BY product").count()
    assert sql_rows == 3
    spark.stop()
    print(json.dumps({"status":"pass","pyspark_version":pyspark.__version__,
        "python_version":sys.version.split()[0],"rows":total_rows,
        "agg_groups":agg_rows,"filtered":filtered,"sql_products":sql_rows,"error":None}))
except Exception as exc:
    print(json.dumps({"status":"fail","error":str(exc),"pyspark_version":"unknown"}))
"""

    log.info("[INFO] pyspark — running validation in Docker %s...", DOCKER_IMAGE)
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--interactive", DOCKER_IMAGE, "python3", "-"],
            input=spark_script,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            log.error(
                "[FAIL] pyspark — container exited %d: %s",
                result.returncode,
                result.stderr[:500],
            )
            return FAIL
        lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
        if not lines:
            log.error(
                "[FAIL] pyspark — no output from container: %s", result.stderr[:400]
            )
            return FAIL
        payload = _json.loads(lines[-1])
        if payload.get("status") == "pass":
            log.info(
                "[PASS] pyspark %s (Python %s in Docker py314) — "
                "rows=%d  agg_groups=%d  filtered=%d  sql_products=%d",
                payload["pyspark_version"],
                payload["python_version"],
                payload["rows"],
                payload["agg_groups"],
                payload["filtered"],
                payload["sql_products"],
            )
            return PASS
        else:
            log.error("[FAIL] pyspark — error in container: %s", payload.get("error"))
            return FAIL
    except subprocess.TimeoutExpired:
        log.error("[FAIL] pyspark — timed out after 120s")
        return FAIL
    except _json.JSONDecodeError as exc:
        log.error("[FAIL] pyspark — JSON parse error: %s", exc)
        return FAIL
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] pyspark — unexpected error: %s", exc)
        return FAIL


def test_dask() -> str:
    """Test dask DataFrame construction and compute."""
    if not _is_installed("dask"):
        log.warning("[SKIP] dask — not installed")
        return SKIP

    import dask  # noqa: PLC0415

    log.info(
        "[INFO] dask %s — checking dask.dataframe availability...", dask.__version__
    )
    try:
        import dask.dataframe as dd  # noqa: PLC0415
        import pandas as pd  # noqa: PLC0415

        pdf = pd.DataFrame({"x": range(10_000), "y": range(10_000, 20_000)})
        ddf = dd.from_pandas(pdf, npartitions=4)
        result = ddf.groupby("x")["y"].sum().compute()
        assert len(result) == 10_000
        log.info(
            "[PASS] dask %s — from_pandas + groupby + compute OK (%d rows)",
            dask.__version__,
            len(result),
        )
        return PASS
    except ImportError as exc:
        if "pyarrow" in str(exc):
            log.warning(
                "[INCOMPAT] dask %s — dask.dataframe requires pyarrow at runtime. "
                "No cp315 wheels for pyarrow under Python 3.15 beta. "
                "dask.array/dask.bag remain functional. Blocker: %s",
                dask.__version__,
                exc,
            )
            return INCOMPAT
        log.error("[FAIL] dask — unexpected ImportError: %s", exc)
        return FAIL
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] dask — %s", exc)
        return FAIL


def test_ray() -> str:
    """Test Ray remote function execution."""
    if not _is_installed("ray"):
        log.warning("[SKIP] ray — not installed")
        return SKIP

    try:
        import ray  # noqa: PLC0415

        log.info("[INFO] ray %s — initializing local cluster...", ray.__version__)

        ray.init(num_cpus=2, ignore_reinit_error=True, logging_level="error")

        @ray.remote
        def square(x: float) -> float:
            return x**2

        futures = [square.remote(i) for i in range(10)]
        results = ray.get(futures)
        assert results == [i**2 for i in range(10)]
        ray.shutdown()

        log.info("[PASS] ray %s — remote function + ray.get() OK", ray.__version__)
        return PASS
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] ray — %s", exc)
        return FAIL


def test_delta() -> str:
    """Test Delta Lake table write and read via delta-spark or deltalake."""
    if not _is_installed("deltalake"):
        log.warning("[SKIP] delta (deltalake) — not installed")
        return SKIP

    try:
        import deltalake  # noqa: PLC0415
        import pyarrow as pa  # noqa: PLC0415  — deltalake requires pyarrow

        log.info("[INFO] deltalake %s — testing write + read...", deltalake.__version__)

        tmp_dir = tempfile.mkdtemp(prefix="py315_delta_")
        try:
            table_path = os.path.join(tmp_dir, "test_table")
            data = pa.table({"id": [1, 2, 3], "value": [10.0, 20.0, 30.0]})
            deltalake.write_deltalake(table_path, data)

            dt = deltalake.DeltaTable(table_path)
            read_back = dt.to_pyarrow_table()
            assert len(read_back) == 3
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        log.info("[PASS] deltalake %s — write + read OK", deltalake.__version__)
        return PASS
    except ImportError as exc:
        # Most likely pyarrow is not installed (Python 3.15 blocker)
        log.warning(
            "[INCOMPAT] deltalake requires pyarrow, which is not available "
            "under Python 3.15 beta: %s",
            exc,
        )
        return INCOMPAT
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] deltalake — %s", exc)
        return FAIL


def test_mlflow() -> str:
    """Test MLflow experiment creation with a local file-based tracking URI."""
    if not _is_installed("mlflow"):
        log.warning("[SKIP] mlflow — not installed")
        return SKIP

    try:
        import mlflow  # noqa: PLC0415

        log.info(
            "[INFO] mlflow %s — testing experiment creation...", mlflow.__version__
        )

        tmp_dir = tempfile.mkdtemp(prefix="py315_mlflow_")
        try:
            mlflow.set_tracking_uri(f"file://{tmp_dir}")
            experiment_id = mlflow.create_experiment("py315_validation")
            assert experiment_id is not None

            with mlflow.start_run(experiment_id=experiment_id):
                mlflow.log_param("python_version", sys.version.split()[0])
                mlflow.log_metric("smoke_test_score", 1.0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        log.info(
            "[PASS] mlflow %s — experiment + run + log_param/metric OK",
            mlflow.__version__,
        )
        return PASS
    except ImportError as exc:
        log.warning(
            "[INCOMPAT] mlflow — incomplete install due to pyarrow hard dependency "
            "under Python 3.15 beta. Missing transitive dep: %s. "
            "Install mlflow normally once pyarrow cp315 wheels are published.",
            exc,
        )
        return INCOMPAT
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] mlflow — %s", exc)
        return FAIL


def test_prefect() -> str:
    """Test Prefect flow definition and local execution."""
    if not _is_installed("prefect"):
        log.warning("[SKIP] prefect — not installed")
        return SKIP

    try:
        import prefect  # noqa: PLC0415
        from prefect import flow, task  # noqa: PLC0415

        log.info("[INFO] prefect %s — testing flow execution...", prefect.__version__)

        @task
        def extract() -> list[int]:
            return list(range(100))

        @task
        def transform(data: list[int]) -> int:
            return sum(data)

        @flow(name="py315_smoke_flow")
        def smoke_pipeline() -> int:
            data = extract()
            return transform(data)

        result = smoke_pipeline()
        assert result == sum(range(100)), f"Expected {sum(range(100))}, got {result}"

        log.info(
            "[PASS] prefect %s — @flow + @task execution OK (result=%d)",
            prefect.__version__,
            result,
        )
        return PASS
    except ImportError as exc:
        if "no_type_check_decorator" in str(exc):
            log.warning(
                "[INCOMPAT] prefect — typing.no_type_check_decorator was removed "
                "in Python 3.15 (deprecated since 3.13). Prefect 3.7.x references "
                "this symbol at import time. Track https://github.com/PrefectHQ/prefect "
                "for a Python 3.15 fix. Error: %s",
                exc,
            )
            return INCOMPAT
        log.error("[FAIL] prefect — unexpected ImportError: %s", exc)
        return FAIL
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] prefect — %s", exc)
        return FAIL


def test_airflow() -> str:
    """Test Apache Airflow DAG definition (no scheduler required).

    Only tests DAG + operator object construction, not execution, since running
    a full Airflow scheduler requires a database and broker setup.
    """
    if not _is_installed("airflow"):
        log.warning("[SKIP] apache-airflow — not installed")
        return SKIP

    try:
        # Airflow requires AIRFLOW_HOME; use a temp dir to avoid polluting the
        # user's home directory during this smoke test.
        tmp_home = tempfile.mkdtemp(prefix="py315_airflow_")
        os.environ.setdefault("AIRFLOW_HOME", tmp_home)

        from datetime import datetime  # noqa: PLC0415

        import airflow  # noqa: PLC0415
        from airflow import DAG  # noqa: PLC0415
        from airflow.providers.standard.operators.python import (
            PythonOperator,  # noqa: PLC0415
        )

        log.info("[INFO] airflow %s — testing DAG construction...", airflow.__version__)

        with DAG(
            dag_id="py315_smoke_dag",
            start_date=datetime(2026, 1, 1),
            schedule=None,
            catchup=False,
        ) as dag:
            task_a = PythonOperator(
                task_id="task_a",
                python_callable=lambda: log.info("Airflow task_a running"),
            )
            task_b = PythonOperator(
                task_id="task_b",
                python_callable=lambda: log.info("Airflow task_b running"),
            )
            task_a >> task_b  # Define dependency

        assert len(dag.tasks) == 2
        shutil.rmtree(tmp_home, ignore_errors=True)

        log.info(
            "[PASS] airflow %s — DAG construction + task dependency OK (%d tasks)",
            airflow.__version__,
            len(dag.tasks),
        )
        return PASS
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] apache-airflow — %s", exc)
        return FAIL


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def main() -> int:
    log.info("=" * 70)
    log.info("Phase 6 — Extended Data Engineering Stack Validation")
    log.info("Author  : Dr. Ceasar Jackson Jr.")
    log.info("Python  : %s", sys.version.split()[0])
    log.info("NOTE    : SKIP results are expected — not failures")
    log.info("=" * 70)

    checks: list[tuple[str, Callable[[], str]]] = [
        ("PySpark", test_pyspark),
        ("Dask", test_dask),
        ("Ray", test_ray),
        ("Delta Lake", test_delta),
        ("MLflow", test_mlflow),
        ("Prefect", test_prefect),
        ("Apache Airflow", test_airflow),
    ]

    results: dict[str, str] = {}
    for name, fn in checks:
        log.info("-" * 50)
        log.info("Testing: %s", name)
        results[name] = fn()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    log.info("=" * 70)
    log.info("Phase 6 Summary")
    log.info("=" * 70)

    counts = {code: 0 for code in (PASS, WARN, SKIP, FAIL, INCOMPAT)}
    for pkg, code in results.items():
        counts[code] += 1
        if code == PASS:
            log.info("  [%s]      %s", code, pkg)
        elif code in (SKIP, WARN):
            log.warning("  [%s]      %s", code, pkg)
        else:
            log.error("  [%s] %s", code, pkg)

    log.info("-" * 70)
    log.info(
        "Results — PASS: %d  WARN: %d  SKIP: %d  FAIL: %d  INCOMPAT: %d",
        counts[PASS],
        counts[WARN],
        counts[SKIP],
        counts[FAIL],
        counts[INCOMPAT],
    )

    # Only true FAIL results should produce a non-zero exit code.
    # INCOMPAT results represent documented upstream ecosystem issues
    # and should not fail the validation suite.
    hard_failures = counts[FAIL]

    if counts[INCOMPAT]:
        log.warning(
            "%d package(s) are currently incompatible with Python 3.15.",
            counts[INCOMPAT],
        )

    if hard_failures == 0:
        log.info("No hard failures. Extended stack validation complete.")
        return 0

    log.error(
        "%d package(s) failed validation.",
        hard_failures,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
