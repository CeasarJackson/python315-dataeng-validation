"""
test_airflow_version.py
Airflow version detection and core import validation.
Python 3.15 notes:
  - Airflow 3.2.2 is fully compatible with Python 3.15.0b2
  - PythonOperator/BashOperator moved to airflow.providers.standard
  - days_ago() removed in Airflow 3.x; use datetime arithmetic instead
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
