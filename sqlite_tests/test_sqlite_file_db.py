"""
===============================================================================
test_sqlite_file_db.py — SQLite file-based database under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlite_tests/test_sqlite_file_db.py

Purpose
-------
Validate Sqlite compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlite_tests/test_sqlite_file_db.py

Validation
----------
python -m py_compile sqlite_tests/test_sqlite_file_db.py
python -m ruff check sqlite_tests/test_sqlite_file_db.py
python -m black --check sqlite_tests/test_sqlite_file_db.py
python -m pytest sqlite_tests/test_sqlite_file_db.py

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

import pathlib
import sqlite3


def test_sqlite_file_create_and_read(tmp_path):
    """SQLite creates a file-based DB, writes data, and reads it back."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    assert pathlib.Path(db_path).exists()
    conn2 = sqlite3.connect(db_path)
    val = conn2.execute("SELECT x FROM t").fetchone()[0]
    conn2.close()
    assert val == 42


def test_sqlite_file_persistence(tmp_path):
    """SQLite data persists across connection open/close cycles."""
    db_path = str(tmp_path / "persist.db")
    for i in range(3):
        conn = sqlite3.connect(db_path)
        if i == 0:
            conn.execute("CREATE TABLE t (n INTEGER)")
        conn.execute("INSERT INTO t VALUES (?)", (i,))
        conn.commit()
        conn.close()
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    conn.close()
    assert count == 3
