"""
===============================================================================
test_sqlalchemy_reflection.py — SQLAlchemy schema reflection.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlalchemy_tests/test_sqlalchemy_reflection.py

Purpose
-------
Validate Sqlalchemy compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlalchemy_tests/test_sqlalchemy_reflection.py

Validation
----------
python -m py_compile sqlalchemy_tests/test_sqlalchemy_reflection.py
python -m ruff check sqlalchemy_tests/test_sqlalchemy_reflection.py
python -m black --check sqlalchemy_tests/test_sqlalchemy_reflection.py
python -m pytest sqlalchemy_tests/test_sqlalchemy_reflection.py

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

from sqlalchemy import create_engine, text, inspect


def test_sqlalchemy_reflect_table_names():
    """SQLAlchemy reflects table names from an existing schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE foo (id INTEGER)"))
        conn.execute(text("CREATE TABLE bar (name TEXT)"))
        conn.commit()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "foo" in tables
    assert "bar" in tables


def test_sqlalchemy_reflect_columns():
    """SQLAlchemy reflects column names and types."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, salary REAL)"
            )
        )
        conn.commit()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("employees")}
    assert cols == {"id", "name", "salary"}
