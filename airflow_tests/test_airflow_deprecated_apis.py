"""
===============================================================================
test_airflow_deprecated_apis.py — Airflow 3.x API change validation.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : airflow_tests/test_airflow_deprecated_apis.py

Purpose
-------
Validate Airflow compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest airflow_tests/test_airflow_deprecated_apis.py

Validation
----------
python -m py_compile airflow_tests/test_airflow_deprecated_apis.py
python -m ruff check airflow_tests/test_airflow_deprecated_apis.py
python -m black --check airflow_tests/test_airflow_deprecated_apis.py
python -m pytest airflow_tests/test_airflow_deprecated_apis.py

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

import warnings
import pytest


def test_airflow_operators_deprecated_path_warns():
    """Old operator import path emits DeprecatedImportWarning in Airflow 3.x."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from airflow.operators.python import PythonOperator  # noqa: F401

        deprecated = any("DeprecatedImportWarning" in str(x.category) for x in w)
    assert deprecated, "Expected DeprecatedImportWarning for legacy operator path"


def test_airflow_providers_standard_operators_available():
    """New providers.standard operator path is available in Airflow 3.x."""
    from airflow.providers.standard.operators.python import PythonOperator
    from airflow.providers.standard.operators.bash import BashOperator

    assert PythonOperator is not None
    assert BashOperator is not None


def test_airflow_days_ago_removed():
    """days_ago is removed from airflow.utils.dates in Airflow 3.x."""
    with pytest.raises(ImportError):
        from airflow.utils.dates import days_ago  # noqa: F401
