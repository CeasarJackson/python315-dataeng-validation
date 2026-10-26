# Python 3.15.1 - Baseline vs Reconciled

**Status:** PROVISIONAL - reference comparison, not an official release score
**Evidence date:** 2026-10-26
**Baseline:** `manifest.baseline.json` (unchanged)
**Reconciled:** `manifest.reconciled.json`

## Readiness

Baseline **17%** -> reconciled **94%**.

Formula: round(100 * (PASS + 0.50 * BLOCKED + 0.25 * INCOMPAT) / (TOTAL - SKIP)). The score is a weighted package-compatibility indicator, not production readiness.

| Status | Baseline | Reconciled | Delta |
|---|---:|---:|---:|
| PASS | 1 | 15 | +14 |
| FAIL | 9 | 0 | -9 |
| INCOMPAT | 0 | 0 | +0 |
| BLOCKED | 2 | 2 | +0 |
| SKIP | 5 | 0 | -5 |
| Total | 17 | 17 | |

## Changes by kind

| Kind | Packages |
|---|---:|
| improvement | 10 |
| regression | 0 |
| coverage | 5 |
| unchanged | 2 |
| new | 0 |

## Package detail

| Package | Baseline | Reconciled | Change | Version | Evidence level | Reason / note |
|---|---|---|---|---|---|---|
| numpy | FAIL | PASS | improvement | not installed -> 2.5.4 | Functional |  |
| pandas | FAIL | PASS | improvement | not installed -> 3.1.0 | Functional |  |
| polars | FAIL | PASS | improvement | not installed -> 1.41.2 | Functional |  |
| duckdb | FAIL | PASS | improvement | not installed -> 2.0.0 | Functional |  |
| sqlalchemy | FAIL | PASS | improvement | not installed -> 2.0.50 | Functional |  |
| pydantic | FAIL | PASS | improvement | not installed -> 2.14.1 | Functional |  |
| matplotlib | FAIL | PASS | improvement | not installed -> 3.11.2 | Functional |  |
| plotly | FAIL | PASS | improvement | not installed -> 6.7.0 | Functional |  |
| jupyterlab | FAIL | PASS | improvement | not installed -> 4.5.7 | Integration |  |
| sqlite3 | PASS | PASS | unchanged | 3.54.1 -> 3.54.1 | Functional |  |
| pyarrow | BLOCKED | PASS | improvement | unavailable -> 26.0.0 | Functional |  |
| dask.dataframe | SKIP | PASS | coverage | not installed -> 2026.7.1 | Integration |  |
| prefect | SKIP | PASS | coverage | not installed -> 3.9.0 | Functional | EventsWorker log errors reproduce identically on Python 3.14.10; not attributable to 3.15.1; root cause undetermined |
| mlflow | SKIP | BLOCKED | coverage | not installed -> 3.17.2 | Resolution | Upstream pin pyarrow<26 plus no cp315 wheel for pyarrow 25.x. Workarounds: mlflow-skinny passes core tracking; full mlflow with a pyarrow>=26 override passes core, sklearn, dataset and table probes but fails uv pip check |
| ray | BLOCKED | BLOCKED | unchanged | unavailable -> unavailable | Resolution | no cp315 wheels on the configured index |
| pyspark | SKIP | PASS | coverage | unknown -> 4.2.0 | Functional | Local mode only; PyArrow/pandas-backed features and cluster mode not tested |
| apache-airflow | SKIP | PASS | coverage | not installed -> 3.3.2 | Functional | dags test runs tasks in-process; scheduler and api-server not exercised. Binary-only resolution fails only because PyYAML 6.0.3 is sdist-only (source build passed 5/5 checks) |

## Standard applied

A workload actually executed on Python 3.15.1 (evidence_level Functional or Integration).

## Integrity

- Baseline `manifest.baseline.json` SHA-256: `5fa738dcf5606f3e2f59a8c08fd23b9b2181cdb685ad4fabd24f145aad49f8f6`
- Evidence `evidence.json` SHA-256: `9f4875b3d0bca540f4f2254d56b0fe12b202d4277e5ceaccccac4e2e1e3945e8`
