"""
==============================================================================
Project: Python 3.15 Data Engineering Validation Suite
Author: Dr. Ceasar Jackson Jr.

Purpose:
    Opt-in Docker integration regression tests for Python 3.15.1,
    PySpark, PyArrow, pandas UDFs, and advanced Spark schemas.

Usage:
    RUN_DOCKER_INTEGRATION=1 .venv3151/bin/python -m pytest \\
        tests/test_pyspark_arrow_integration.py -v

Prerequisites:
    Docker daemon and pyarrow-dataeng:py315 image.

Validation:
    python -m py_compile tests/test_pyspark_arrow_integration.py
    python -m pytest tests/test_pyspark_arrow_integration.py -v

Safety:
    Docker networking disabled; no host volumes mounted.
    No repository files modified by the tests.
==============================================================================
"""

from __future__ import annotations

import os
import subprocess

import pytest

IMAGE = "pyarrow-dataeng:py315"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("RUN_DOCKER_INTEGRATION") != "1",
        reason="Set RUN_DOCKER_INTEGRATION=1 to run Docker integration tests",
    ),
]


def test_pyspark_arrow_advanced_interoperability() -> None:
    """Validate Spark schemas, Arrow nulls, and a pandas UDF."""

    probe = """
import sys
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import pyarrow
import pyspark
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    ArrayType,
    DecimalType,
    DoubleType,
    IntegerType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

assert sys.version_info[:3] == (3, 15, 1)

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("py315_regression")
    .config("spark.ui.enabled", "false")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.execution.arrow.pyspark.enabled", "true")
    .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    assert spark.conf.get(
        "spark.sql.execution.arrow.pyspark.enabled"
    ) == "true"

    assert spark.conf.get(
        "spark.sql.execution.arrow.pyspark.fallback.enabled"
    ) == "false"

    nested = spark.createDataFrame(
        [(1, ("alpha", 30)), (2, (None, None))],
        StructType([
            StructField("id", IntegerType(), False),
            StructField(
                "person",
                StructType([
                    StructField("name", StringType(), True),
                    StructField("age", IntegerType(), True),
                ]),
                True,
            ),
        ]),
    ).collect()

    assert nested[0].person.name == "alpha"
    assert nested[1].person.name is None

    arrays = spark.createDataFrame(
        [(1, [1, None, 3]), (2, [])],
        StructType([
            StructField("id", IntegerType(), False),
            StructField(
                "values",
                ArrayType(IntegerType(), containsNull=True),
                True,
            ),
        ]),
    ).collect()

    assert arrays[0].values == [1, None, 3]
    assert arrays[1].values == []

    maps = spark.createDataFrame(
        [(1, {"a": 10, "b": None}), (2, {})],
        StructType([
            StructField("id", IntegerType(), False),
            StructField(
                "attributes",
                MapType(StringType(), IntegerType(), valueContainsNull=True),
                True,
            ),
        ]),
    ).collect()

    assert maps[0].attributes["b"] is None
    assert maps[1].attributes == {}

    instant = datetime(2026, 10, 26, 12, 30, 45, tzinfo=timezone.utc)

    timestamps = spark.createDataFrame(
        [(1, instant), (2, None)],
        StructType([
            StructField("id", IntegerType(), False),
            StructField("event_time", TimestampType(), True),
        ]),
    ).collect()

    assert timestamps[0].event_time == instant.replace(tzinfo=None)
    assert timestamps[1].event_time is None

    decimals = spark.createDataFrame(
        [(1, Decimal("123456.7890")), (2, None)],
        StructType([
            StructField("id", IntegerType(), False),
            StructField("amount", DecimalType(18, 4), True),
        ]),
    ).collect()

    assert decimals[0].amount == Decimal("123456.7890")
    assert decimals[1].amount is None

    source = pd.DataFrame({
        "name": ["alpha", None, "gamma"],
        "value": [1.5, None, 3.5],
    })

    schema = StructType([
        StructField("name", StringType(), True),
        StructField("value", DoubleType(), True),
    ])

    sdf = spark.createDataFrame(source, schema=schema)
    result = sdf.toPandas()

    assert result["name"].isna().sum() == 1
    assert result["value"].isna().sum() == 1
    assert set(result["name"].dropna()) == {"alpha", "gamma"}

    @F.pandas_udf("double")
    def plus_one(series: pd.Series) -> pd.Series:
        return series + 1.0

    values = sdf.select(plus_one("value").alias("v")).toPandas()["v"]

    assert values.isna().sum() == 1
    assert sorted(values.dropna()) == [2.5, 4.5]

    print("PASS: Advanced Spark schemas")
    print("PASS: Arrow null preservation")
    print("PASS: pandas UDF")
    print("PASS: Python", sys.version.split()[0])
    print("PASS: PySpark", pyspark.__version__)
    print("PASS: PyArrow", pyarrow.__version__)

finally:
    spark.stop()
"""

    command = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network",
        "none",
        "--hostname",
        "localhost",
        "--add-host",
        "localhost:127.0.0.1",
        "-e",
        "SPARK_LOCAL_IP=127.0.0.1",
        "-e",
        "SPARK_LOCAL_HOSTNAME=localhost",
        "--memory",
        "4g",
        "--cpus",
        "4",
        "--entrypoint",
        "python3",
        IMAGE,
        "-",
    ]

    completed = subprocess.run(
        command,
        input=probe,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, (
        f"Docker exit code: {completed.returncode}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}"
    )

    assert "PASS: pandas UDF" in completed.stdout
    assert "PASS: Arrow null preservation" in completed.stdout
