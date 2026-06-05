"""
test_airflow_dag.py
DAG construction and operator validation under Python 3.15.
Uses Airflow 3.x APIs (providers.standard.*).
"""
import sys
from datetime import datetime, timedelta

print("=" * 60)
print("AIRFLOW DAG VALIDATION")
print("=" * 60)
print(f"Python: {sys.version.split()[0]}")

import airflow
print(f"Airflow: {airflow.__version__}")

# Core DAG import
from airflow import DAG
print("DAG import: PASS")

# Airflow 3.x operator paths
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator
print("PythonOperator (providers.standard): PASS")
print("BashOperator   (providers.standard): PASS")

# DAG construction — Airflow 3.x uses datetime directly (days_ago removed)
dag = DAG(
    dag_id="py315_validation_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["python315", "validation"],
)
print("DAG instantiation: PASS")

# Task construction
def validate_python():
    import sys
    assert sys.version_info >= (3, 15), f"Expected Python 3.15+, got {sys.version}"
    return f"Python {sys.version.split()[0]} validated"

task_py = PythonOperator(
    task_id="validate_python_version",
    python_callable=validate_python,
    dag=dag,
)
print("PythonOperator task creation: PASS")

task_bash = BashOperator(
    task_id="validate_bash",
    bash_command="echo 'Airflow BashOperator on Python 3.15'",
    dag=dag,
)
print("BashOperator task creation: PASS")

# Task dependency
task_py >> task_bash
print("Task dependency (>>): PASS")

# DAG structure validation
assert dag.dag_id == "py315_validation_dag"
assert len(dag.tasks) == 2
assert task_py.task_id == "validate_python_version"
print(f"DAG structure: PASS  ({len(dag.tasks)} tasks)")

print()
print("DAG VALIDATION: PASS")
