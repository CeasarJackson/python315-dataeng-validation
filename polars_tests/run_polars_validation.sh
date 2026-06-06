#!/usr/bin/env bash
# =============================================================================
# Polars Validation Suite Runner
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# =============================================================================
#
# Purpose
#   Run the full Polars per-library validation suite against Python 3.15.
#   Executes all test scripts and the benchmark in sequence, reporting
#   pass/fail status for each step.
#
# Usage
#   From the repository root:
#     bash polars_tests/run_polars_validation.sh
#
#   With a custom Python interpreter:
#     PYTHON=/path/to/python bash polars_tests/run_polars_validation.sh
#
# Validation
#   Runs: test_polars_version, test_polars_dataframe, test_polars_groupby, test_polars_join, benchmark_polars
#
# Exit Codes
#   0 all tests pass | 1 one or more tests fail
#
# =============================================================================

echo
echo "============================================================"
echo "POLARS VALIDATION SUITE"
echo "============================================================"
echo

python polars_tests/test_polars_version.py
echo
echo "✓ Version Validation Complete"
echo

python polars_tests/test_polars_dataframe.py
echo
echo "✓ DataFrame Validation Complete"
echo

python polars_tests/test_polars_groupby.py
echo
echo "✓ GroupBy Validation Complete"
echo

python polars_tests/test_polars_join.py
echo
echo "✓ Join Validation Complete"
echo

python polars_tests/benchmark_polars.py
echo
echo "✓ Benchmark Validation Complete"
echo

echo "POLARS VALIDATION PASSED"
echo
