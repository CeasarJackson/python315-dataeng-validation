# Compatibility Report — Python 3.15.2

> **SUPERSEDED (2026-10-27):** This report records the original import-probe run of the core environment (88% readiness, PASS 11 / FAIL 1 / BLOCKED 1 / SKIP 4) and is kept as historical evidence. The current provisional result is 94% (PASS 15 / BLOCKED 2) in `manifest.json`; see `READINESS_RECONCILIATION_2026-10-27.md` and `COMPARISON_baseline_vs_reconciled.md`. The original manifest is preserved unchanged as `manifest.baseline.json`.

**Date:** October 27, 2026
**Platform:** macOS 27.0.1 arm64
**Tester:** Dr. Ceasar Jackson Jr.
**Suite Version:** 1.2.0

---

## Summary

| Metric | Value |
|--------|-------|
| Packages Tested | 17 |
| PASS | 11 |
| INCOMPAT | 0 |
| BLOCKED | 1 |
| SKIP | 4 |
| FAIL | 1 |

---

## Core Stack

| Package | Version | Result | Notes |
|---------|---------|--------|-------|
| numpy | 2.5.4 | ✅ PASS |  |
| pandas | 3.1.0 | ✅ PASS |  |
| polars | 1.41.2 | ✅ PASS |  |
| duckdb | 2.0.0 | ✅ PASS |  |
| sqlalchemy | 2.0.50 | ✅ PASS |  |
| pydantic | 2.14.1 | ✅ PASS |  |
| matplotlib | 3.11.2 | ✅ PASS |  |
| plotly | 6.7.0 | ✅ PASS |  |
| jupyterlab | not installed | ❌ FAIL |  |
| sqlite3 | 3.54.1 | ✅ PASS |  |

## Extended Stack

| Package | Version | Result | Notes |
|---------|---------|--------|-------|
| pyspark | 4.2.0 | ✅ PASS | via Docker image pyarrow-dataeng:py3152 (Python 3.15.2) + OpenJDK 21 |
| dask.dataframe | not installed | ⏭️ SKIP |  |
| pyarrow | 26.0.0 | ✅ PASS |  |
| mlflow | not installed | ⏭️ SKIP |  |
| prefect | not installed | ⏭️ SKIP |  |
| ray | unavailable | 🚫 BLOCKED | no cp315 wheels on PyPI |
| apache-airflow | not installed | ⏭️ SKIP | not installed |

---

## Changes from Previous Cycle

*Compare with previous report using:*
```bash
python scripts/compare_reports.py <previous> 3.15.2
```

---

*Generated 2026-10-27 by Python 3.15 Data Engineering Validation Suite v1.2.0*