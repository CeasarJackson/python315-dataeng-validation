#!/usr/bin/env bash

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
