"""
===============================================================================
test_duckdb_pandas.py — DuckDB integration with Pandas under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : duckdb_tests/test_duckdb_pandas.py

Purpose
-------
Validate Duckdb compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest duckdb_tests/test_duckdb_pandas.py

Validation
----------
python -m py_compile duckdb_tests/test_duckdb_pandas.py
python -m ruff check duckdb_tests/test_duckdb_pandas.py
python -m black --check duckdb_tests/test_duckdb_pandas.py
python -m pytest duckdb_tests/test_duckdb_pandas.py

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

import duckdb
import pandas as pd


def test_duckdb_query_pandas_dataframe():
    """DuckDB queries a Pandas DataFrame directly via SQL."""
    duckdb_df = pd.DataFrame(
        {
            "department": ["IT", "IT", "HR", "HR", "Finance"],
            "salary": [100000, 120000, 75000, 80000, 90000],
        }
    )

    duckdb.register("duckdb_df", duckdb_df)
    try:
        result = duckdb.sql("""
            SELECT department, AVG(salary) AS avg_salary
            FROM duckdb_df
            GROUP BY department
            ORDER BY avg_salary DESC
            """).df()
    finally:
        duckdb.unregister("duckdb_df")

    assert list(result["department"]) == ["IT", "Finance", "HR"]
    assert list(result["avg_salary"]) == [110000, 90000, 77500]


def test_duckdb_pandas_roundtrip():
    """DuckDB converts query results back to a Pandas DataFrame."""
    duckdb_df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    duckdb.register("duckdb_df", duckdb_df)
    try:
        result = duckdb.sql("SELECT x, y, x + y AS z FROM duckdb_df").df()
    finally:
        duckdb.unregister("duckdb_df")

    assert list(result.columns) == ["x", "y", "z"]
    assert list(result["z"]) == [5, 7, 9]
