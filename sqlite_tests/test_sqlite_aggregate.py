"""
===============================================================================
test_sqlite_aggregate.py — SQLite aggregate queries under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlite_tests/test_sqlite_aggregate.py

Purpose
-------
Validate Sqlite compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlite_tests/test_sqlite_aggregate.py

Validation
----------
python -m py_compile sqlite_tests/test_sqlite_aggregate.py
python -m ruff check sqlite_tests/test_sqlite_aggregate.py
python -m black --check sqlite_tests/test_sqlite_aggregate.py
python -m pytest sqlite_tests/test_sqlite_aggregate.py

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

import sqlite3


def _make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE nums (n REAL)")
    conn.executemany("INSERT INTO nums VALUES (?)", [(float(i),) for i in range(1, 6)])
    conn.commit()
    return conn


def test_sqlite_sum():
    """SQLite SUM returns the correct total."""
    conn = _make_db()
    result = conn.execute("SELECT SUM(n) FROM nums").fetchone()[0]
    assert result == 15.0
    conn.close()


def test_sqlite_avg():
    """SQLite AVG returns the correct average."""
    conn = _make_db()
    result = conn.execute("SELECT AVG(n) FROM nums").fetchone()[0]
    assert result == 3.0
    conn.close()


def test_sqlite_count():
    """SQLite COUNT returns the correct row count."""
    conn = _make_db()
    result = conn.execute("SELECT COUNT(n) FROM nums").fetchone()[0]
    assert result == 5
    conn.close()


def test_sqlite_min_max():
    """SQLite MIN and MAX return boundary values."""
    conn = _make_db()
    row = conn.execute("SELECT MIN(n), MAX(n) FROM nums").fetchone()
    assert row[0] == 1.0
    assert row[1] == 5.0
    conn.close()
