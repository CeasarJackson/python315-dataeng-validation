"""test_airflow_models.py — Airflow model imports under Python 3.15."""

from airflow.models import DAG, TaskInstance, DagRun
from airflow.utils.state import DagRunState, TaskInstanceState


def test_airflow_dag_model_import():
    """Airflow DAG model imports successfully."""
    assert DAG is not None


def test_airflow_task_instance_import():
    """Airflow TaskInstance imports successfully."""
    assert TaskInstance is not None


def test_airflow_dagrun_import():
    """Airflow DagRun imports successfully."""
    assert DagRun is not None


def test_airflow_dagrun_state_constants():
    """DagRunState exposes SUCCESS, FAILED, and RUNNING."""
    assert hasattr(DagRunState, "SUCCESS")
    assert hasattr(DagRunState, "FAILED")
    assert hasattr(DagRunState, "RUNNING")


def test_airflow_task_instance_state_constants():
    """TaskInstanceState exposes SUCCESS and FAILED."""
    assert hasattr(TaskInstanceState, "SUCCESS")
    assert hasattr(TaskInstanceState, "FAILED")
