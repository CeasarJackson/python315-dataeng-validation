#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : docker/pyarrow_lab_py315/smoke_test.py

Purpose
-------
Build-time smoke test for the py315 probe image. Confirms the container really
runs Python 3.15, that PySpark can start a local session, and that a Python UDF
runs on a worker with the same interpreter as the driver.

Usage
-----
    python3 /workspace/smoke_test.py          # run inside the image

Exit Codes
----------
0   All checks passed.
1   A check failed (the image build stops).
===============================================================================
"""

from __future__ import annotations

import sys


def main() -> int:
    if sys.version_info[:3] != (3, 15, 1):
        print(f"FAIL: expected Python 3.15.1, got {sys.version.split()[0]}")
        return 1

    import pyarrow
    import pyspark
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType

    spark = (
        SparkSession.builder.master("local[1]")
        .appName("py315_smoke")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "768m")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    try:
        df = spark.createDataFrame([(1, "ok"), (2, "ok")], ["id", "s"])
        if df.count() != 2:
            print("FAIL: DataFrame count")
            return 1

        # The UDF body runs in a worker process; it reports its own interpreter.
        worker_python = F.udf(lambda _: sys.version.split()[0], StringType())
        seen = df.select(worker_python("id").alias("v")).distinct().collect()
        worker_versions = {row.v for row in seen}
        driver_version = sys.version.split()[0]
        if worker_versions != {driver_version}:
            print(f"FAIL: worker {worker_versions} != driver {driver_version}")
            return 1
    finally:
        spark.stop()

    print(
        f"PASS: Python {sys.version.split()[0]}, PySpark {pyspark.__version__}, "
        f"PyArrow {pyarrow.__version__}, UDF worker matches driver"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
