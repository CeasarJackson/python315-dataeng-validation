"""
===============================================================================
test_sqlalchemy_orm.py — SQLAlchemy ORM under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlalchemy_tests/test_sqlalchemy_orm.py

Purpose
-------
Validate Sqlalchemy compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlalchemy_tests/test_sqlalchemy_orm.py

Validation
----------
python -m py_compile sqlalchemy_tests/test_sqlalchemy_orm.py
python -m ruff check sqlalchemy_tests/test_sqlalchemy_orm.py
python -m black --check sqlalchemy_tests/test_sqlalchemy_orm.py
python -m pytest sqlalchemy_tests/test_sqlalchemy_orm.py

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

from sqlalchemy import create_engine, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    salary: Mapped[float]


def test_sqlalchemy_orm_insert_and_query():
    """SQLAlchemy ORM inserts and queries objects."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Employee(id=1, name="Alice", salary=100000),
                Employee(id=2, name="Bob", salary=125000),
            ]
        )
        session.commit()
        employees = session.query(Employee).order_by(Employee.salary.desc()).all()
    assert len(employees) == 2
    assert employees[0].name == "Bob"
    assert employees[1].name == "Alice"


def test_sqlalchemy_orm_filter():
    """SQLAlchemy ORM filters objects by attribute."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Employee(id=3, name="Charlie", salary=95000),
                Employee(id=4, name="Dana", salary=110000),
            ]
        )
        session.commit()
        high = session.query(Employee).filter(Employee.salary > 100000).all()
    assert len(high) == 1
    assert high[0].name == "Dana"
