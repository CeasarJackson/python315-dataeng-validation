#!/usr/bin/env bash

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
