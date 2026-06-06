from datetime import datetime
import sys
import time

import airflow
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

print("AIRFLOW BENCHMARK")
print(f"Python  : {sys.version.split()[0]}")
print(f"Airflow : {airflow.__version__}")
print()


def noop():
    pass


# Benchmark: DAG instantiation
N_DAGS = 100
t0 = time.perf_counter()
for i in range(N_DAGS):
    dag = DAG(
        dag_id=f"bench_dag_{i}",
        start_date=datetime(2026, 1, 1),
        schedule=None,
    )
elapsed = time.perf_counter() - t0
print(
    f"DAG instantiation x{N_DAGS}   : {elapsed*1000:.1f} ms  ({elapsed/N_DAGS*1000:.2f} ms/dag)"
)

# Benchmark: task creation
N_TASKS = 500
dag = DAG("bench_tasks", start_date=datetime(2026, 1, 1), schedule=None)
t0 = time.perf_counter()
tasks = []
for i in range(N_TASKS):
    t = PythonOperator(
        task_id=f"task_{i}",
        python_callable=noop,
        dag=dag,
    )
    tasks.append(t)
elapsed = time.perf_counter() - t0
print(
    f"Task creation x{N_TASKS}      : {elapsed*1000:.1f} ms  ({elapsed/N_TASKS*1000:.2f} ms/task)"
)

# Benchmark: task chaining
t0 = time.perf_counter()
for i in range(len(tasks) - 1):
    tasks[i] >> tasks[i + 1]
elapsed = time.perf_counter() - t0
print(f"Task chaining x{N_TASKS-1}    : {elapsed*1000:.1f} ms")

print()
print("BENCHMARK: COMPLETE")
