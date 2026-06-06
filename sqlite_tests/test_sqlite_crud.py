"""
===============================================================================
test_sqlite_crud.py — SQLite CRUD operations under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlite_tests/test_sqlite_crud.py

Purpose
-------
Validate Sqlite compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlite_tests/test_sqlite_crud.py

Validation
----------
python -m py_compile sqlite_tests/test_sqlite_crud.py
python -m ruff check sqlite_tests/test_sqlite_crud.py
python -m black --check sqlite_tests/test_sqlite_crud.py
python -m pytest sqlite_tests/test_sqlite_crud.py

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


def test_sqlite_create_insert_select():
    """SQLite creates a table, inserts rows, and queries them."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
    conn.executemany("INSERT INTO t VALUES (?,?)", [(1, "Alice"), (2, "Bob")])
    conn.commit()
    rows = conn.execute("SELECT * FROM t ORDER BY id").fetchall()
    assert len(rows) == 2
    assert rows[0] == (1, "Alice")
    assert rows[1] == (2, "Bob")
    conn.close()


def test_sqlite_update():
    """SQLite updates a row correctly."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER, val INTEGER)")
    conn.execute("INSERT INTO t VALUES (1, 10)")
    conn.commit()
    conn.execute("UPDATE t SET val = 99 WHERE id = 1")
    conn.commit()
    val = conn.execute("SELECT val FROM t WHERE id = 1").fetchone()[0]
    assert val == 99
    conn.close()


def test_sqlite_delete():
    """SQLite deletes a row correctly."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.executemany("INSERT INTO t VALUES (?)", [(1,), (2,), (3,)])
    conn.commit()
    conn.execute("DELETE FROM t WHERE id = 2")
    conn.commit()
    rows = conn.execute("SELECT id FROM t ORDER BY id").fetchall()
    assert [r[0] for r in rows] == [1, 3]
    conn.close()
