"""test_airflow_deprecated_apis.py — Airflow 3.x API change validation."""
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
