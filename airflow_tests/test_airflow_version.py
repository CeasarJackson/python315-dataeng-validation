"""
===============================================================================
test_airflow_version.py
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : airflow_tests/test_airflow_version.py

Purpose
-------
Validate Airflow compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest airflow_tests/test_airflow_version.py

Validation
----------
python -m py_compile airflow_tests/test_airflow_version.py
python -m ruff check airflow_tests/test_airflow_version.py
python -m black --check airflow_tests/test_airflow_version.py
python -m pytest airflow_tests/test_airflow_version.py

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

import sys

import airflow


def test_airflow_import_and_version():
    """Validate Airflow imports successfully and exposes a version."""
    print("=" * 60)
    print("AIRFLOW VERSION VALIDATION")
    print("=" * 60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Airflow version : {airflow.__version__}")
    print(f"Import path     : {airflow.__file__}")

    assert airflow.__version__
    assert airflow.__file__ is not None
