"""
===============================================================================
test_sqlite_version.py — SQLite version and import validation.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlite_tests/test_sqlite_version.py

Purpose
-------
Validate Sqlite compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlite_tests/test_sqlite_version.py

Validation
----------
python -m py_compile sqlite_tests/test_sqlite_version.py
python -m ruff check sqlite_tests/test_sqlite_version.py
python -m black --check sqlite_tests/test_sqlite_version.py
python -m pytest sqlite_tests/test_sqlite_version.py

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


def test_sqlite_version():
    """sqlite3 module exposes the SQLite engine version."""
    assert sqlite3.sqlite_version
    parts = sqlite3.sqlite_version.split(".")
    assert len(parts) == 3
    assert int(parts[0]) >= 3


def test_sqlite_in_memory_connection():
    """sqlite3 connects to an in-memory database."""
    conn = sqlite3.connect(":memory:")
    assert conn is not None
    conn.close()
