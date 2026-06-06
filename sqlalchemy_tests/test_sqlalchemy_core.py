"""test_sqlalchemy_core.py — SQLAlchemy Core API under Python 3.15."""
from sqlalchemy import create_engine, text


def test_sqlalchemy_in_memory_engine():
    """SQLAlchemy creates an in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    assert engine is not None


def test_sqlalchemy_core_crud():
    """SQLAlchemy Core executes CREATE, INSERT, SELECT correctly."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER, val TEXT)"))
        conn.execute(text("INSERT INTO t VALUES (1,'alpha'),(2,'beta')"))
        conn.commit()
        rows = conn.execute(text("SELECT * FROM t ORDER BY id")).fetchall()
    assert len(rows) == 2
    assert rows[0].id == 1
    assert rows[0].val == "alpha"
    assert rows[1].val == "beta"


def test_sqlalchemy_core_aggregation():
    """SQLAlchemy Core runs aggregation queries."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE nums (n INTEGER)"))
        conn.execute(text("INSERT INTO nums VALUES (:n)"), [{"n": i} for i in range(1, 6)])
        conn.commit()
        result = conn.execute(text("SELECT SUM(n), COUNT(n) FROM nums")).fetchone()
    assert result[0] == 15   # 1+2+3+4+5
    assert result[1] == 5
