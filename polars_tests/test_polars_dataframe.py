"""
===============================================================================
test_polars_dataframe.py — Polars DataFrame operations under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : polars_tests/test_polars_dataframe.py

Purpose
-------
Validate Polars compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest polars_tests/test_polars_dataframe.py

Validation
----------
python -m py_compile polars_tests/test_polars_dataframe.py
python -m ruff check polars_tests/test_polars_dataframe.py
python -m black --check polars_tests/test_polars_dataframe.py
python -m pytest polars_tests/test_polars_dataframe.py

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

import polars as pl


def test_polars_filter():
    """Polars filters rows correctly."""
    df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
    result = df.filter(pl.col("x") > 3)
    assert len(result) == 2
    assert result["x"].to_list() == [4, 5]


def test_polars_select():
    """Polars selects and renames columns."""
    df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = df.select(pl.col("a").alias("x"))
    assert result.columns == ["x"]
    assert result["x"].to_list() == [1, 2]


def test_polars_with_columns():
    """Polars adds a computed column."""
    df = pl.DataFrame({"x": [1, 2, 3]})
    result = df.with_columns((pl.col("x") * 2).alias("y"))
    assert result["y"].to_list() == [2, 4, 6]
