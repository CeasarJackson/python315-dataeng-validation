#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-.venv/bin/python}"

echo
echo "============================================================"
echo "AIRFLOW VALIDATION SUITE"
echo "Apache Airflow $(${PYTHON} -c 'import airflow; print(airflow.__version__)')"
echo "Python $(${PYTHON} --version 2>&1 | cut -d' ' -f2)"
echo "============================================================"
echo

${PYTHON} airflow_tests/test_airflow_version.py
echo
echo "✓ Version Validation Complete"
echo

${PYTHON} airflow_tests/test_airflow_dag.py
echo
echo "✓ DAG Validation Complete"
echo

${PYTHON} airflow_tests/test_airflow_models.py
echo
echo "✓ Models Validation Complete"
echo

${PYTHON} airflow_tests/test_airflow_deprecated_apis.py
echo
echo "✓ Deprecated API Documentation Complete"
echo

${PYTHON} airflow_tests/benchmark_airflow.py
echo
echo "✓ Benchmark Complete"
echo
echo "AIRFLOW VALIDATION PASSED"
echo
