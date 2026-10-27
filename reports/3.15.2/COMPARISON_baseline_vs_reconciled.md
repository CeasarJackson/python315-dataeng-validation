# Python 3.15.2 - Baseline vs Reconciled

**Status:** PROVISIONAL - reference comparison, not an official release score
**Evidence date:** 2026-10-27
**Baseline:** `manifest.baseline.json` (unchanged)
**Reconciled:** `manifest.reconciled.json`

## Readiness

Baseline **88%** -> reconciled **94%**.

Formula: round(100 * (PASS + 0.50 * BLOCKED + 0.25 * INCOMPAT) / (TOTAL - SKIP)). The score is a weighted package-compatibility indicator, not production readiness.

| Status | Baseline | Reconciled | Delta |
|---|---:|---:|---:|
| PASS | 11 | 15 | +4 |
| FAIL | 1 | 0 | -1 |
| INCOMPAT | 0 | 0 | +0 |
| BLOCKED | 1 | 2 | +1 |
| SKIP | 4 | 0 | -4 |
| Total | 17 | 17 | |

## Changes by kind

| Kind | Packages |
|---|---:|
| improvement | 1 |
| regression | 0 |
| coverage | 4 |
| unchanged | 12 |
| new | 0 |

## Package detail

| Package | Baseline | Reconciled | Change | Version | Evidence level | Reason / note |
|---|---|---|---|---|---|---|
| numpy | PASS | PASS | unchanged | 2.5.4 -> 2.5.4 | Functional |  |
| pandas | PASS | PASS | unchanged | 3.1.0 -> 3.1.0 | Functional |  |
| polars | PASS | PASS | unchanged | 1.41.2 -> 1.41.2 | Functional |  |
| duckdb | PASS | PASS | unchanged | 2.0.0 -> 2.0.0 | Functional |  |
| sqlalchemy | PASS | PASS | unchanged | 2.0.50 -> 2.0.50 | Functional |  |
| pydantic | PASS | PASS | unchanged | 2.14.1 -> 2.14.1 | Functional |  |
| matplotlib | PASS | PASS | unchanged | 3.11.2 -> 3.11.2 | Functional |  |
| plotly | PASS | PASS | unchanged | 6.7.0 -> 6.7.0 | Functional |  |
| jupyterlab | FAIL | PASS | improvement | not installed -> 4.6.4 | Integration | No persistent server session tested; the kernel logged an unencrypted-TCP-transport warning. Version differs from 3.15.1 (4.5.7). |
| sqlite3 | PASS | PASS | unchanged | 3.54.1 -> 3.54.1 | Functional |  |
| pyarrow | PASS | PASS | unchanged | 26.0.0 -> 26.0.0 | Functional |  |
| dask.dataframe | SKIP | PASS | coverage | not installed -> 2026.7.1 | Integration | dask/config.py opens a file without encoding=, which raises EncodingWarning under -X warn_default_encoding (an error with -W error). Upstream, informational. |
| prefect | SKIP | PASS | coverage | not installed -> 3.9.0 | Functional | Prefect 3.7.x is unusable: it requires starlette>=1.0.1 but calls Body(min_items=...), which FastAPI 0.162.0 rejects, and no FastAPI satisfying starlette>=1.0.1 and accepting it resolves; 3.9.0 resolves with FastAPI 0.150.0. Some runs log a telemetry-heartbeat 'database is locked' error (absent with telemetry disabled) and intermittent EventsWorker errors. The EventsWorker errors reproduced identically on Python 3.14.10 with the same Prefect version during the 3.15.1 cycle (not rerun for 3.15.2); root cause undetermined; results were correct in every run. |
| mlflow | SKIP | BLOCKED | coverage | not installed -> unavailable | Resolution | Upstream pin pyarrow<26 (every release from 3.15.0) plus no cp315 wheel for pyarrow 25.x; pyarrow 26.0.0, which has one, is excluded by the cap. The 3.15.1 workarounds (mlflow-skinny; full mlflow with a pyarrow>=26 override, which fails uv pip check) and the pyarrow 25.x source-build failure were not re-run on 3.15.2. |
| ray | BLOCKED | BLOCKED | unchanged | unavailable -> unavailable | Resolution | no cp315 wheels on the configured index |
| pyspark | PASS | PASS | unchanged | 4.2.0 -> 4.2.0 | Functional | Local mode only; cluster mode not tested. Evidence is from the py3152 Docker image, not the macOS venv. |
| apache-airflow | SKIP | PASS | coverage | not installed -> 3.3.2 | Functional | dags test runs tasks in-process; scheduler and api-server not exercised. Binary-only resolution fails only because PyYAML 6.0.3 is sdist-only; the install builds it from source (libcst 1.9.0 resolved). |

## Standard applied

A workload actually executed on Python 3.15.2 (evidence_level Functional or Integration).

## Integrity

- Baseline `manifest.baseline.json` SHA-256: `b7e4668ed29cec839640243d69e34f88756b6e154f1f65832aa55f6feee6889a`
- Evidence `evidence.json` SHA-256: `04bae52bb4b1c411b0c1cdc5d167afb4e9c6b61f6adbfdf9367c2b3db7b25c7f`
