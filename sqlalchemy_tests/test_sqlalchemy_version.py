"""
===============================================================================
test_sqlalchemy_version.py — SQLAlchemy version and import validation.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : sqlalchemy_tests/test_sqlalchemy_version.py

Purpose
-------
Validate Sqlalchemy compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest sqlalchemy_tests/test_sqlalchemy_version.py

Validation
----------
python -m py_compile sqlalchemy_tests/test_sqlalchemy_version.py
python -m ruff check sqlalchemy_tests/test_sqlalchemy_version.py
python -m black --check sqlalchemy_tests/test_sqlalchemy_version.py
python -m pytest sqlalchemy_tests/test_sqlalchemy_version.py

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

import sqlalchemy


def test_sqlalchemy_version():
    """SQLAlchemy exposes a version string."""
    assert sqlalchemy.__version__


def test_sqlalchemy_core_imports():
    """SQLAlchemy core components import successfully."""
    from sqlalchemy import create_engine, text

    assert create_engine
    assert text
