"""
===============================================================================
test_duckdb_basic.py — DuckDB basic SQL validation under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : duckdb_tests/test_duckdb_basic.py

Purpose
-------
Validate Duckdb compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest duckdb_tests/test_duckdb_basic.py

Validation
----------
python -m py_compile duckdb_tests/test_duckdb_basic.py
python -m ruff check duckdb_tests/test_duckdb_basic.py
python -m black --check duckdb_tests/test_duckdb_basic.py
python -m pytest duckdb_tests/test_duckdb_basic.py

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


def test_duckdb_version():
    """DuckDB imports and exposes a version string."""
    assert duckdb.__version__


def test_duckdb_in_memory_connection():
    """DuckDB connects to an in-memory database."""
    con = duckdb.connect(":memory:")
    assert con is not None
    con.close()


def test_duckdb_create_and_query():
    """DuckDB creates a table, inserts rows, and returns correct results."""
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE employees(id INTEGER, name VARCHAR, salary DOUBLE)
    """)
    con.execute("""
        INSERT INTO employees VALUES
        (1,'Alice',100000),(2,'Bob',125000),(3,'Charlie',95000)
    """)
    rows = con.execute("""
        SELECT * FROM employees ORDER BY salary DESC
    """).fetchall()
    assert len(rows) == 3
    assert rows[0][1] == "Bob"  # highest salary
    assert rows[0][2] == 125000.0
    assert rows[-1][1] == "Charlie"  # lowest salary
    con.close()


def test_duckdb_aggregation():
    """DuckDB executes aggregation queries correctly."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE nums AS SELECT * FROM range(1, 101) t(n)")
    result = con.execute("SELECT SUM(n), AVG(n), COUNT(n) FROM nums").fetchone()
    assert result[0] == 5050  # sum 1..100
    assert result[1] == 50.5  # avg
    assert result[2] == 100  # count
    con.close()
