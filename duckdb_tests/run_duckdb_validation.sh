#!/usr/bin/env bash
# =============================================================================
# DuckDB Validation Suite Runner
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# =============================================================================
#
# Purpose
#   Run the full DuckDB per-library validation suite against Python 3.15.
#   Executes all test scripts and the benchmark in sequence, reporting
#   pass/fail status for each step.
#
# Usage
#   From the repository root:
#     bash duckdb_tests/run_duckdb_validation.sh
#
#   With a custom Python interpreter:
#     PYTHON=/path/to/python bash duckdb_tests/run_duckdb_validation.sh
#
# Validation
#   Runs: test_duckdb_basic, test_duckdb_pandas, test_duckdb_native_parquet, benchmark_duckdb
#
# Exit Codes
#   0 all tests pass | 1 one or more tests fail
#
# =============================================================================

set -euo pipefail

echo
echo "============================================================"
echo "DUCKDB VALIDATION SUITE"
echo "============================================================"
echo

python duckdb_tests/test_duckdb_basic.py

echo
echo "✓ Basic SQL Validation Complete"
echo

python duckdb_tests/test_duckdb_pandas.py

echo
echo "✓ Pandas Integration Complete"
echo

python duckdb_tests/test_duckdb_native_parquet.py

echo
echo "✓ Native Parquet Write Complete"
echo

python duckdb_tests/verify_duckdb_parquet.py

echo
echo "✓ Native Parquet Read Complete"
echo

python duckdb_tests/benchmark_duckdb.py

echo
echo "✓ Benchmark Complete"
echo
echo "DUCKDB VALIDATION PASSED"
echo
