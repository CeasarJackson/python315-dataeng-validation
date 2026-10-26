# Python 3.15.1 — Readiness Reconciliation (v2)

**Author:** Ceasar Jackson
**Assessment date:** 2026-10-26
**Document generated:** 2026-10-26 20:12:03 UTC (16:12 EDT); revised later the same day
**Platform:** macOS arm64
**Interpreter:** CPython 3.15.1
**Status:** PROVISIONAL — NOT AN OFFICIAL RELEASE SCORE
**Supersedes (does not replace):** READINESS_RECONCILIATION_2026-10-26.md (96%)

## Executive Summary

The original Python 3.15.1 baseline recorded 17% readiness and is preserved.
The first reconciliation produced a provisional 96% with four packages
still unevaluated. After isolated-environment testing of those four packages,
this revision records a provisional **94%** weighted package-compatibility
score, with 15 PASS, 2 BLOCKED and 0 SKIP out of 17 entries.

The score is not a measure of production readiness, security, performance or
operational reliability.

## Status Standard Applied

PASS requires a workload actually executed on Python 3.15.1 in an isolated or
documented environment. Lower evidence is recorded at its true level and is not
scored as PASS.

| Level | Meaning |
|---|---|
| Resolution | Dependency resolver succeeds (wheels and/or source builds) |
| Install | Package installs; `uv pip check` clean |
| Import | Package imports on 3.15.1 |
| Functional | Package performs real work in a scripted test |
| Integration | Multiple components work together |
| Production | Not assessed anywhere in this project |

Rules: a resolver success is never a PASS; a failed install caused by an
upstream pin or missing wheel is BLOCKED, not INCOMPAT; test-design errors are
not counted against a package; baselines and prior reports are never rewritten.

## Readiness Calculation

Formula:

Readiness = 100 * (PASS + 0.50 * BLOCKED + 0.25 * INCOMPAT)
            / (TOTAL - SKIP)

| Status | Baseline | Reconciliation v1 | v2 |
|---|---:|---:|---:|
| PASS | 1 | 12 | 15 |
| BLOCKED | 2 | 1 | 2 |
| INCOMPAT | 0 | 0 | 0 |
| FAIL | 9 | 0 | 0 |
| SKIP | 5 | 4 | 0 |
| Total | 17 | 17 | 17 |
| **Score** | **17%** | **96%** | **94%** |

Sensitivity: holding Airflow at SKIP would also give 94% (14 PASS, 2 BLOCKED,
1 SKIP, 16 in the denominator). Accepting the MLflow `pyarrow>=26` override as
PASS would give 97% (16 PASS, 1 BLOCKED).

## Package-Level Reconciliation

| Package | Original | v2 | Version | Highest evidence | Evidence |
|---|---|---|---|---|---|
| numpy | FAIL | PASS | 2.5.4 | Functional | Core functional validation |
| pandas | FAIL | PASS | 3.1.0 | Functional | Core functional validation |
| polars | FAIL | PASS | 1.41.2 | Functional | Core functional validation |
| duckdb | FAIL | PASS | 2.0.0 | Functional | Core functional validation |
| sqlalchemy | FAIL | PASS | 2.0.50 | Functional | Core functional validation |
| pydantic | FAIL | PASS | 2.14.1 | Functional | Core functional validation |
| matplotlib | FAIL | PASS | 3.11.2 | Functional | Core rendering validation |
| plotly | FAIL | PASS | 6.7.0 | Functional | Core figure construction |
| jupyterlab | FAIL | PASS | 4.5.7 | Integration | Install, import, notebook execution, kernel isolation |
| sqlite3 | PASS | PASS | 3.54.1 | Functional | Baseline validation |
| pyarrow | BLOCKED | PASS | 26.0.0 | Functional | Arrow/Parquet round-trip |
| dask.dataframe | SKIP | PASS | 2026.7.1 | Integration | DataFrame integration incl. Arrow/Parquet |
| prefect | SKIP | PASS | 3.9.0 | Functional | Isolated env; flow, task, retry (4/4 checks); EventsWorker log errors reproduced on Python 3.14.10 |
| pyspark | SKIP | PASS | 4.2.0 | Functional | Isolated env, local[1], JDK 21; DataFrame ops, Python UDF, worker Python 3.15.1 |
| mlflow | SKIP | BLOCKED | 3.17.2 | Resolution/build | Stock install fails: upstream pin pyarrow<26 and no cp315 wheel for 25.x. Workarounds below |
| ray | BLOCKED | BLOCKED | 2.59.0 (no cp315 wheel) | Resolution | Binary-only resolve fails; source builds not evaluated |
| apache-airflow | SKIP | PASS | 3.3.2 | Functional | Isolated env, 129 packages, integrity clean; `db migrate`; two-task DAG (extract -> transform, XCom 120) run via `airflow dags test`, state success, exit 0. Scheduler and api-server not run |

## Decisions and Rationale

- **Prefect (PASS).** Installed in an isolated env (103 packages, integrity clean);
  four functional checks passed. Repeated `EventsWorker failed with N pending items`
  log errors reproduce identically on Python 3.14.10 with the same Prefect and
  websockets versions, so they are not attributable to Python 3.15.1. Root cause
  inside Prefect's event client or the ephemeral server is undetermined.
- **PySpark (PASS).** Local mode only. The first job failure was a driver/worker
  interpreter mismatch caused by unset `PYSPARK_PYTHON`, a test-setup error.
  After pinning, DataFrame operations, a Python UDF and a worker version check
  all passed. PyArrow/pandas-backed features and cluster mode were not tested.
- **MLflow (BLOCKED).** MLflow 3.17.2, the latest release, declares
  `pyarrow<26,>=4.0.0`. The resolver selected pyarrow 25.0.1, which has no usable
  cp315 wheel, and its source build failed (no Arrow C++, no ninja).
  Workarounds recorded, neither equivalent to a supported install:
  - `mlflow-skinny` 3.17.2: installs cleanly, core tracking passes (file store
    requires `MLFLOW_ALLOW_FILE_STORE=true`; no SQL backends).
  - Full `mlflow` with a `pyarrow>=26` override: core tracking, sklearn
    log/load, dataset logging and `log_table` pass, but `uv pip check` fails
    because the override violates MLflow's metadata.
- **Ray (BLOCKED).** Unchanged: no cp315 wheel on the configured index.
- **Apache Airflow (PASS).** Installed (129 packages, integrity clean), imported
  (3.3.2), `db migrate` and `dags list` exit 0 on a temporary SQLite home.
  A DAG with two dependent `@task` functions was discovered and executed with
  `airflow dags test python_3151_validation 2026-10-26`; both tasks ran, XCom
  values passed between them (`[10, 20, 30]` then `120`), the task code confirmed
  Python 3.15.1, and the run finished `state=success` with exit 0. `dags test`
  executes tasks in-process, so the scheduler and api-server were not exercised.
  Warnings observed: argparse `FileType` deprecation (appears to be the Python
  3.14+ argparse deprecation raised in Airflow's CLI code), missing graphviz,
  and a Starlette `httpx` deprecation; none caused a failure.
  Binary-only resolution for Airflow fails only because PyYAML 6.0.3 is
  published solely as a source distribution; the PyYAML source build passed
  5/5 checks.
- **Root cause shared across Airflow/LibCST binary-only failures:** PyYAML has no
  cp315 wheel in any release. LibCST 1.9.0 itself has a cp315 macOS arm64 wheel.

## Limitations

- Evidence is terminal output supplied by the tester; this document's author
  did not execute the tests. Wheel availability was cross-checked on PyPI
  (2026-10-26).
- Temporary environments under `/var/folders/.../T/` and `/tmp` may be removed.
- Source-build outcomes depend on the local toolchain and uv cache state.
- Not tested anywhere: production Jupyter, distributed Dask, Spark cluster mode,
  Airflow scheduler and api-server, MLflow server/registry, performance, security.
- SKIP entries are excluded from the score denominator.
- Repository tests: 147 passed on Python 3.15.1 against a throwaway copy of
  the working tree. `tests/test_readiness_consistency.py` has `REPORT_DIR`
  hardcoded to `reports/3.15.0`, so it does not evaluate the 3.15.1 reports;
  `tests/test_report_completeness.py` iterates every `3.15.*` release with a
  manifest and therefore includes 3.15.1. No test checks the 94% figure.

## Recommended Follow-Up

1. Exercise Airflow's scheduler and api-server in a persistent run before any production claim; `dags test` does not cover them.
2. Revalidate Ray wheel availability when a cp315 release appears.
3. Re-test MLflow when it relaxes the `pyarrow` pin, or document the override.
4. Do not regenerate the official artifacts by simply running
   `scripts/generate_report.py`. It probes only the active interpreter's
   environment with imports (Prefect and Airflow reach PASS on import or DAG
   construction, below this document's standard), classifies missing imports as
   SKIP or BLOCKED, maps a `uv pip check` violation to INCOMPAT (the MLflow
   override would be misreported), and probes PySpark through a Docker image
   (`pyarrow-dataeng:py314`) rather than 3.15.1. The validated packages live in
   separate isolated environments, which one run cannot see. Either extend the
   generator to ingest an evidence file or build the official manifest from the
   table above and use `tools/sync_readiness.py`; both are code or methodology
   decisions for the owner. Keep scaffolded 0% files marked non-authoritative.
5. Re-run the focused tests after any code change (147 passed on 3.15.1 as of this revision).

## Machine-Readable Form

The package table above is also recorded as data and can be regenerated and
compared without hand editing:

- `evidence.json` — evidence per package (status, version, evidence level,
  evidence, reason/note). SHA-256 `9f4875b3d0bca540f4f2254d56b0fe12b202d4277e5ceaccccac4e2e1e3945e8`.
- `manifest.reconciled.json` — reconciled manifest in the same schema as
  `manifest.json` plus a `reconciliation` block (provenance and hashes).
- `COMPARISON_baseline_vs_reconciled.md` — baseline (17%) versus reconciled
  (94%) by package.
- Produced by `scripts/ingest_evidence.py --release 3.15.1`; validated by
  `tests/test_ingest_evidence.py`, which pins the readiness formula to
  `tools/sync_readiness.py` and the adopted 94%.

The original 17% manifest is preserved byte-for-byte as `manifest.baseline.json`
(SHA-256 below; originally committed as `manifest.json` in 2c8d603). The ingest
script reads it by default and never writes it. After review, `manifest.json`
was promoted to the reconciled data and now reports 94% (PROVISIONAL).

## Revision Note

Revised 2026-10-26 after the first v2 write: the Airflow `dags test` result
(supplied by the tester) moved Airflow from held SKIP to PASS under the stated
standard. Score 94% is unchanged (it was 94% under both treatments).
A later revision corrected the Prefect/MLflow report hash below (that report
gained a reading guide), added the repository-tests and generator findings, and
fixed the generation timestamp label. A further revision added the
Machine-Readable Form section. A final revision, made when the official
manifest was promoted to 94%, moved the ingest baseline to the frozen
`manifest.baseline.json` (promotion had silently changed the old baseline
input and broke a test) and added a hash-pin test for it.

## Evidence Integrity (SHA-256 at generation time)

- manifest.baseline.json (original manifest.json, commit 2c8d603): 5fa738dcf5606f3e2f59a8c08fd23b9b2181cdb685ad4fabd24f145aad49f8f6
- compatibility_report.md (as of 2c8d603; a superseded notice was added later): 472ff72be51a6e12dfa5a259788b17650661c8e4521ebee90af39578de682f2f
- CORE_STACK_VALIDATION_2026-10-26.md: b807bad41ebb96c0736147c4d98b6a68e37bd52ddcf64c4ec8ef1d58a3d8bffe
- EXTENDED_STACK_VALIDATION_2026-10-26.md: 279099badaa2ad10d7186affe1b28a6750dd9b49fcf56f1e7e74afd82d559a03
- READINESS_RECONCILIATION_2026-10-26.md: 48aa4e576d3027834257b5402277ffebf68880901ad13bc0dd27f067cc041963
- PREFECT_MLFLOW_VALIDATION_2026-10-26.md: eb72b1367dc35ce346e92efca4619f20a486a68161771fc4f6cf42ff811ca2ab

The source reports were read but not modified. The original manifest readiness
remains 17%.

**Checkpoint result: PROVISIONAL 94% WEIGHTED COMPATIBILITY.**
