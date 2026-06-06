"""test_sqlalchemy_transactions.py — SQLAlchemy transaction handling."""
from sqlalchemy import create_engine, text


def test_sqlalchemy_commit():
    """SQLAlchemy commits a transaction and persists data."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (x INTEGER)"))
        conn.execute(text("INSERT INTO t VALUES (1)"))
        conn.commit()
        count = conn.execute(text("SELECT COUNT(*) FROM t")).scalar()
    assert count == 1


def test_sqlalchemy_rollback():
    """SQLAlchemy rolls back a transaction on error."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (x INTEGER)"))
        conn.commit()
        try:
            with conn.begin():
                conn.execute(text("INSERT INTO t VALUES (99)"))
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass
        count = conn.execute(text("SELECT COUNT(*) FROM t")).scalar()
    assert count == 0
