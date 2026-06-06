"""test_sqlite_version.py — SQLite version and import validation."""
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
