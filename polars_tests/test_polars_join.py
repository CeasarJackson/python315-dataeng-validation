"""
===============================================================================
test_polars_join.py — Polars join operations under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : polars_tests/test_polars_join.py

Purpose
-------
Validate Polars compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest polars_tests/test_polars_join.py

Validation
----------
python -m py_compile polars_tests/test_polars_join.py
python -m ruff check polars_tests/test_polars_join.py
python -m black --check polars_tests/test_polars_join.py
python -m pytest polars_tests/test_polars_join.py

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


def test_polars_inner_join():
    """Polars inner join returns only matching rows."""
    left = pl.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    right = pl.DataFrame({"id": [2, 3, 4], "dept": ["HR", "IT", "Finance"]})
    result = left.join(right, on="id", how="inner")
    assert len(result) == 2
    assert set(result["name"].to_list()) == {"Bob", "Charlie"}


def test_polars_left_join():
    """Polars left join retains all left rows."""
    left = pl.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    right = pl.DataFrame({"id": [1, 2], "label": ["a", "b"]})
    result = left.join(right, on="id", how="left")
    assert len(result) == 3
    assert result.filter(pl.col("id") == 3)["label"][0] is None


def test_polars_join_column_count():
    """Polars join produces the correct number of columns."""
    a = pl.DataFrame({"k": [1, 2], "x": ["a", "b"]})
    b = pl.DataFrame({"k": [1, 2], "y": ["c", "d"]})
    result = a.join(b, on="k", how="inner")
    assert set(result.columns) == {"k", "x", "y"}
