#!/usr/bin/env bash

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
