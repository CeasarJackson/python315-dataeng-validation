"""
test_airflow_models.py
Core model imports and metadata access under Python 3.15.
"""
import sys

print("=" * 60)
print("AIRFLOW MODELS VALIDATION")
print("=" * 60)
print(f"Python: {sys.version.split()[0]}")

from airflow.models import DAG, TaskInstance, DagRun
print("DAG model import        : PASS")
print("TaskInstance import     : PASS")
print("DagRun import           : PASS")

from airflow.models.baseoperator import BaseOperator
print("BaseOperator import     : PASS")

from airflow.utils.state import DagRunState, TaskInstanceState
print("DagRunState import      : PASS")
print("TaskInstanceState import: PASS")

# Validate state constants
assert hasattr(DagRunState, "SUCCESS")
assert hasattr(DagRunState, "FAILED")
assert hasattr(DagRunState, "RUNNING")
print("DagRunState constants   : PASS")

assert hasattr(TaskInstanceState, "SUCCESS")
assert hasattr(TaskInstanceState, "FAILED")
print("TaskInstanceState consts: PASS")

print()
print("MODELS VALIDATION: PASS")
