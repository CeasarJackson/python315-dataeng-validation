"""test_sqlalchemy_reflection.py — SQLAlchemy schema reflection."""

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
