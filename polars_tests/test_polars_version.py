"""
===============================================================================
test_polars_version.py — Polars version and import validation.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : polars_tests/test_polars_version.py

Purpose
-------
Validate Polars compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest polars_tests/test_polars_version.py

Validation
----------
python -m py_compile polars_tests/test_polars_version.py
python -m ruff check polars_tests/test_polars_version.py
python -m black --check polars_tests/test_polars_version.py
python -m pytest polars_tests/test_polars_version.py

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


def test_polars_version():
    """Polars exposes a version string."""
    assert pl.__version__
    parts = pl.__version__.split(".")
    assert len(parts) >= 2


def test_polars_dataframe_creation():
    """Polars creates a DataFrame from a dict."""
    df = pl.DataFrame({"id": [1, 2, 3]})
    assert len(df) == 3
    assert df.columns == ["id"]
