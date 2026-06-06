#!/usr/bin/env bash
# =============================================================================
# SQLite Validation Suite Runner
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# =============================================================================
#
# Purpose
#   Run the full SQLite per-library validation suite against Python 3.15.
#   Executes all test scripts and the benchmark in sequence, reporting
#   pass/fail status for each step.
#
# Usage
#   From the repository root:
#     bash sqlite_tests/run_sqlite_validation.sh
#
#   With a custom Python interpreter:
#     PYTHON=/path/to/python bash sqlite_tests/run_sqlite_validation.sh
#
# Validation
#   Runs: test_sqlite_version, test_sqlite_crud, test_sqlite_aggregate, test_sqlite_file_db, benchmark_sqlite
#
# Exit Codes
#   0 all tests pass | 1 one or more tests fail
#
# =============================================================================

set -euo pipefail

echo
echo "============================================================"
echo "SQLITE VALIDATION SUITE"
echo "============================================================"
echo

python sqlite_tests/test_sqlite_version.py

echo
echo "✓ Version Validation Complete"
echo

python sqlite_tests/test_sqlite_crud.py

echo
echo "✓ CRUD Validation Complete"
echo

python sqlite_tests/test_sqlite_aggregate.py

echo
echo "✓ Aggregation Validation Complete"
echo

python sqlite_tests/test_sqlite_file_db.py

echo
echo "✓ File Database Validation Complete"
echo

python sqlite_tests/benchmark_sqlite.py

echo
echo "✓ Benchmark Validation Complete"
echo
echo "SQLITE VALIDATION PASSED"
echo
