"""
===============================================================================
test_sqlalchemy_transactions.py — SQLAlchemy transaction handling.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlalchemy_tests/test_sqlalchemy_transactions.py

Purpose
-------
Validate Sqlalchemy compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlalchemy_tests/test_sqlalchemy_transactions.py

Validation
----------
python -m py_compile sqlalchemy_tests/test_sqlalchemy_transactions.py
python -m ruff check sqlalchemy_tests/test_sqlalchemy_transactions.py
python -m black --check sqlalchemy_tests/test_sqlalchemy_transactions.py
python -m pytest sqlalchemy_tests/test_sqlalchemy_transactions.py

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
