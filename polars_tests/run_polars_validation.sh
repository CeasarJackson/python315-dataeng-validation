#!/usr/bin/env bash

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
