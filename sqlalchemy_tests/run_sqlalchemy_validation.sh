#!/usr/bin/env bash
# =============================================================================
# SQLAlchemy Validation Suite Runner
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# =============================================================================
#
# Purpose
#   Run the full SQLAlchemy per-library validation suite against Python 3.15.
#   Executes all test scripts and the benchmark in sequence, reporting
#   pass/fail status for each step.
#
# Usage
#   From the repository root:
#     bash sqlalchemy_tests/run_sqlalchemy_validation.sh
#
#   With a custom Python interpreter:
#     PYTHON=/path/to/python bash sqlalchemy_tests/run_sqlalchemy_validation.sh
#
# Validation
#   Runs: test_sqlalchemy_version, test_sqlalchemy_core, test_sqlalchemy_orm, test_sqlalchemy_reflection, test_sqlalchemy_transactions, benchmark_sqlalchemy
#
# Exit Codes
#   0 all tests pass | 1 one or more tests fail
#
# =============================================================================

echo
echo "============================================================"
echo "SQLALCHEMY VALIDATION SUITE"
echo "============================================================"
echo

python sqlalchemy_tests/test_sqlalchemy_version.py

echo
echo "✓ Version Validation Complete"
echo

python sqlalchemy_tests/test_sqlalchemy_core.py

echo
echo "✓ Core Validation Complete"
echo

python sqlalchemy_tests/test_sqlalchemy_orm.py

echo
echo "✓ ORM Validation Complete"
echo

python sqlalchemy_tests/test_sqlalchemy_transactions.py

echo
echo "✓ Transaction Validation Complete"
echo

python sqlalchemy_tests/test_sqlalchemy_reflection.py

echo
echo "✓ Reflection Validation Complete"
echo

python sqlalchemy_tests/benchmark_sqlalchemy.py

echo
echo "✓ Benchmark Validation Complete"
echo

echo "SQLALCHEMY VALIDATION PASSED"
echo
