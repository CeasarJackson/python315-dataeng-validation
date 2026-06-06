"""
===============================================================================
test_airflow_dag.py — Airflow DAG construction under Python 3.15.
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : airflow_tests/test_airflow_dag.py

Purpose
-------
Validate Airflow compatibility, behavior, and regression safety under Python 3.15.

Usage
-----
python -m pytest airflow_tests/test_airflow_dag.py

Validation
----------
python -m py_compile airflow_tests/test_airflow_dag.py
python -m ruff check airflow_tests/test_airflow_dag.py
python -m black --check airflow_tests/test_airflow_dag.py
python -m pytest airflow_tests/test_airflow_dag.py

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

from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator


def test_airflow_dag_instantiation():
    """Airflow DAG instantiates with correct dag_id."""
    dag = DAG("test_dag", start_date=datetime(2026, 1, 1), schedule=None)
    assert dag.dag_id == "test_dag"


def test_airflow_python_operator():
    """PythonOperator creates a task from a callable."""
    dag = DAG("test_py_op", start_date=datetime(2026, 1, 1), schedule=None)
    task = PythonOperator(
        task_id="py_task",
        python_callable=lambda: "ok",
        dag=dag,
    )
    assert task.task_id == "py_task"


def test_airflow_bash_operator():
    """BashOperator creates a task from a bash command."""
    dag = DAG("test_bash_op", start_date=datetime(2026, 1, 1), schedule=None)
    task = BashOperator(
        task_id="bash_task",
        bash_command="echo hello",
        dag=dag,
    )
    assert task.task_id == "bash_task"


def test_airflow_task_dependency():
    """Airflow task dependency (>>) is registered correctly."""
    dag = DAG("test_deps", start_date=datetime(2026, 1, 1), schedule=None)
    t1 = PythonOperator(task_id="t1", python_callable=lambda: None, dag=dag)
    t2 = PythonOperator(task_id="t2", python_callable=lambda: None, dag=dag)
    t1 >> t2
    assert len(dag.tasks) == 2
    assert t2 in t1.downstream_list


def test_airflow_dag_task_count():
    """DAG with multiple tasks reports correct task count."""
    dag = DAG(
        "test_count", start_date=datetime(2026, 1, 1), schedule=None, catchup=False
    )
    for i in range(5):
        PythonOperator(task_id=f"task_{i}", python_callable=lambda: None, dag=dag)
    assert len(dag.tasks) == 5
