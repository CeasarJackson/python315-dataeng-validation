"""test_sqlite_aggregate.py — SQLite aggregate queries under Python 3.15."""
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
