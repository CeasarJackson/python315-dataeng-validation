#!/usr/bin/env bash
# =============================================================================
# Apache Airflow Validation Suite Runner
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# =============================================================================
#
# Purpose
#   Run the full Apache Airflow per-library validation suite against Python 3.15.
#   Executes all test scripts and the benchmark in sequence, reporting
#   pass/fail status for each step.
#
# Usage
#   From the repository root:
#     bash airflow_tests/run_airflow_validation.sh
#
#   With a custom Python interpreter:
#     PYTHON=/path/to/python bash airflow_tests/run_airflow_validation.sh
#
# Validation
#   Runs: test_airflow_version, test_airflow_dag, test_airflow_models, test_airflow_deprecated_apis, benchmark_airflow
#
# Exit Codes
#   0 all tests pass | 1 one or more tests fail
#
# =============================================================================

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
