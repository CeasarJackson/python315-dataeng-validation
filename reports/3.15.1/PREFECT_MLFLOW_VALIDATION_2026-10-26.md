# Python 3.15.1 — Prefect and MLflow Isolated Installation Validation

**Author:** Ceasar Jackson
**Assessment date:** 2026-10-26
**Evidence window:** 13:08–13:52 EDT (terminal output supplied by the tester)
**Platform:** macOS arm64 (AppleClang 21.0.0, CMake 4.4.4)
**Interpreter:** CPython 3.15.1
**Status:** PROVISIONAL — PROPOSED STATUS CHANGES, NOT APPLIED TO ANY MANIFEST

## Reading Guide

This report is chronological: it records each test round as it happened, and
later sections supersede earlier statements. For final statuses and the
score, use `READINESS_RECONCILIATION_2026-10-26_v2.md`. Superseded points:

- "MLflow-skinny was not validated" (14:29 round) is superseded by the 14:33
  follow-up: skinny passes core tracking with `MLFLOW_ALLOW_FILE_STORE=true`.
- "the job has not yet run with a 3.15.1 worker, so PySpark is not validated"
  (14:33 round) is superseded by the 14:49 results: PySpark passes.
- "Airflow ... no install attempted" and the held-SKIP rows are superseded by
  the Airflow install (14:49) and the `airflow dags test` run (16:17), which
  passed; see the v2 reconciliation.
- The score scenario table is a decision aid; the adopted outcome is 94%.

## Executive Summary

Prefect 3.9.0 installed, imported and passed 4 functional checks in an
isolated virtual environment, but its event-reporting service logged
repeated errors during the run that are not yet explained.

MLflow 3.17.2 failed to install. The resolver selected pyarrow 25.0.1,
for which no usable cp315 binary wheel was found, and the source-build
fallback failed because Arrow C++ was not available. This is a
dependency/build-environment blocker, not evidence that MLflow code is
incompatible with Python 3.15.1.

## Method

Each package was installed into its own temporary venv created from
`.venv3151/bin/python`. The `.venv3151` baseline and the repository were
checked before and after. Source builds were permitted in these runs
(unlike the earlier `--only-binary :all:` dry-runs).

## Results

### Prefect 3.9.0 — install and functional validation

| Check | Result |
|---|---|
| Isolated env creation | exit 0 |
| Install | exit 0 — 103 packages resolved and installed |
| `uv pip check` (isolated env) | PASS — 103 packages compatible |
| Import (`prefect`, `flow`, `task`) | PASS |
| Task execution and aggregation (total == 120) | PASS |
| Retry recovery | PASS |
| Retry count (attempts == 2) | PASS |
| Functional test exit code | 0 |
| `.venv3151` baseline after run | PASS — 25 packages compatible |

Notable resolved versions: pydantic 2.14.1, sqlalchemy 2.1.6,
pyyaml 6.0.3, cryptography 50.0.2, orjson 3.13.0, websockets 16.1.1.
This run does not show which of the 103 packages were built from source.

**Anomaly — EventsWorker (diagnosed to a version-independent behavior).**
During the flow run the log repeatedly reported
`Service 'EventsWorker' failed with N pending items`
(GlobalEventLoopThread, prefect._internal.concurrency). Task and flow runs
still finished in state Completed.

Diagnostics performed (13:52–14:01 EDT):

1. The temp `prefect-home` held no `*.log`/`*.jsonl` files and no matches.
2. A minimal one-task flow with `PREFECT_LOGGING_LEVEL=DEBUG` reproduced the
   errors (first one at flow-execution start, then one per event), so the
   retry test is not the cause.
3. `prefect/_internal/concurrency/services.py` logs this message from a
   `BaseException` handler and includes the traceback only when that logger
   passes `isEnabledFor(DEBUG)`.
4. Control run, same probe script, same Prefect 3.9.0 and websockets 16.1.1
   (fresh temp env, ephemeral server):

| Interpreter | Flow exit | EventsWorker error lines |
|---|---:|---:|
| CPython 3.15.1 | 0 | 2 |
| CPython 3.14.10 (Homebrew) | 0 | 2 |

Conclusion: the errors occur identically on Python 3.14.10 and 3.15.1, so
they are **not attributable to Python 3.15.1**. The underlying exception was
not captured (forcing the logger to DEBUG in the probe did not surface a
traceback on either interpreter), so the root cause inside Prefect's event
client or the ephemeral server remains undetermined. Because event delivery
fails on both interpreters while flows complete, treat it as a Prefect 3.9.0
/ ephemeral-server behavior to monitor, not a Python 3.15 compatibility defect.

Scope not covered: persistent server, deployments, workers, schedules,
UI, database backends other than the temporary SQLite store.

### MLflow 3.17.2 — install failure

| Check | Result |
|---|---|
| Isolated env creation | exit 0 |
| Resolution | 87 packages resolved |
| pyyaml 6.0.3 | built from source successfully |
| pyarrow 25.0.1 | source build FAILED (scikit-build-core, CMake) |
| MLflow install exit code | 1 |
| Import / dependency checks | not reached |

Failure cause: `CMake Error at CMakeLists.txt:294 (find_package)` —
no `ArrowConfig.cmake` / `arrow-config.cmake` found. The `pyarrow`
dependency was pulled in by `mlflow` 3.17.2 (uv hint).

Build-environment diagnostic (13:39 EDT):

- `brew list --versions apache-arrow` printed no version (Arrow C++ appears not installed).
- No `ArrowConfig.cmake` / `arrow-config.cmake` under `/opt/homebrew`.
- CMake 4.4.4 present.
- `ninja` not found.
- `.venv3151` already holds PyArrow 26.0.0 (binary), which passed Arrow/Parquet round-trip validation.

Verified constraint (package metadata, read 2026-10-26 14:07 EDT from the
PyPI wheel for mlflow 3.17.2, which is the latest release on the index):

- `mlflow` requires `pyarrow<26,>=4.0.0`.
- `mlflow-skinny==3.17.2` has no base `pyarrow` dependency (only an `extras` extra).
- `.venv3151` uses PyArrow 26.0.0, which is excluded by the pin.
- The resolver therefore selected pyarrow 25.0.1, whose build fell back to
  source; a cp315 wheel for 25.x was not available to the resolver.
- Other base pins to validate later: scikit-learn<2, scipy<2, pandas<4, numpy<3.

Blocker classification: dependency pin (upstream) combined with a missing
cp315 wheel for the pinned PyArrow range. Not an MLflow code defect.

### MLflow 3.17.2 — follow-up runs (14:08–14:10 EDT)

Two isolated envs built from `.venv3151` (temp dir `/tmp/mlflow3151b.hqMnSd`).
Functional probe: set experiment, start run, log one param, one metric and a
dict artifact, read the run back and assert values.

| Case | Install | `uv pip check` | Functional probe |
|---|---|---|---|
| `mlflow-skinny==3.17.2` | exit 0 (41 packages) | PASS | Not valid, see note |
| `mlflow==3.17.2` + override `pyarrow>=26`, `--only-binary pyarrow` | exit 0 (87 packages) | FAIL: 1 incompatibility | PASS (params/metrics/artifact round-trip, SQLite backend) |

Notes:

- Skinny probe error: `UnsupportedModelRegistryStoreURIException` for a
  `sqlite:` URI. Skinny ships without SQLAlchemy, so only file/HTTP stores are
  supported. This is a defect in the test design (wrong backend for skinny),
  not a Python 3.15.1 failure. Skinny has not yet been functionally validated.
- Full install with the override worked on Python 3.15.1 with PyArrow 26.0.0.
  The expected integrity failure is `mlflow requires pyarrow>=4.0.0,<26, but
  26.0.0 is installed`. The override therefore violates MLflow's declared
  metadata, so this is not a supported configuration.
- The full install also resolved scikit-learn, scipy and SQLAlchemy 2.1.6
  without error; the output shown does not say whether any were source-built.
- Not tested: model logging/loading (sklearn flavor), Arrow-dependent dataset
  logging, tracking server/UI, model registry workflows.
- `.venv3151` baseline stayed at 25 compatible packages; `git diff --check` 0.

Interpretation: the stock install remains blocked by the upstream
`pyarrow<26` pin. With the pin overridden, basic tracking works on 3.15.1, so
the pin appears to be the only install blocker, but that is only shown for the
narrow probe above.

### MLflow extended probes and blocker isolation (14:29–14:30 EDT)

**MLflow, full install with the `pyarrow>=26` override** (same env as above;
PyArrow 26.0.0, pandas 3.1.0):

| Probe | Result |
|---|---|
| Core tracking (param, metric, dict artifact, SQLite) | PASS |
| `mlflow.sklearn.log_model` | PASS |
| `mlflow.sklearn.load_model` with predict parity | PASS |
| Dataset logging (`mlflow.data.from_pandas`, `log_input`) | PASS |
| `log_table` | PASS |

Warnings only: pip version not resolved for conda.yaml (the venv has no pip)
and a schema integer-column hint. Still outside the declared `pyarrow<26`
metadata and still failing `uv pip check`.

**MLflow-skinny** was not validated: the file-store rerun was refused because
MLflow 3.17.2 puts the filesystem backend in maintenance mode unless
`MLFLOW_ALLOW_FILE_STORE=true` is set. This is again a test-design error, not
a Python 3.15.1 failure.

**Binary-only dry-runs against `.venv3151` (Airflow/PySpark blockers):**

| Package | Binary-only result | Source allowed |
|---|---|---|
| libcst | resolved to 0.3.0 (exit 0) | not run |
| pyyaml | exit 1; only `pyyaml 5.1b7` with a `cp27` wheel found | already built from source successfully earlier |
| pendulum | 3.3.0 resolves (exit 0) | not run |
| sqlalchemy | no changes needed (exit 0) | not run |
| pyspark | exit 1: "all versions have no usable wheels" | resolves: pyspark 4.2.0 + py4j 0.10.9.9 (exit 0) |
| apache-airflow | previously exit 1 | resolves (exit 0); version and package count not captured |

PyPI metadata checked 2026-10-26 (JSON API, latest releases):

- PyYAML 6.0.3: sdist only, no cp315 wheel in any release.
- PySpark 4.2.0: sdist only, no wheels at all.
- Pendulum 3.3.0: cp315 wheels present, including macOS arm64.
- LibCST 1.9.0: cp315 macOS arm64 wheel exists
  (`libcst-1.9.0-cp315-cp315-macosx_11_0_arm64.whl`), plus cp315t variants.

Findings:

1. PySpark's binary-only failure is a property of how it is published
   (source distribution only), not evidence of Python 3.15 incompatibility.
2. PyYAML has no cp315 wheel anywhere, so any binary-only policy fails any
   package that needs it (confirmed for LibCST >=1.9.0; see follow-up). A source build of PyYAML 6.0.3 has already passed 5/5
   functional checks.
3. Pendulum and SQLAlchemy are not blockers, contradicting the earlier
   suspicion in the handoff.
4. LibCST's earlier result (0.3.0) is explained: 1.9.0 has a cp315 wheel but
   depends on `pyyaml>=6.0.3`, which has no wheel (see follow-up below).
5. Airflow and PySpark resolve when source builds are allowed. Resolution is
   not installation: Airflow's dependency set may need source builds (for
   example LibCST or other native packages) that a dry-run does not exercise.

### Skinny, LibCST and PySpark follow-up (14:33 EDT)

**mlflow-skinny 3.17.2 (no PyArrow, no override):** install exit 0 (41
packages), `uv pip check` PASS, core tracking probe PASS using the file store
with `MLFLOW_ALLOW_FILE_STORE=true` (required because MLflow 3.17.2 puts the
file backend in maintenance mode). Skinny has no SQLAlchemy, so SQL backends
are unavailable. Scope: core tracking only.

**LibCST explained.** `uv pip install --only-binary :all: 'libcst>=1.9.0'`
fails with: `libcst>=1.9.0 depends on pyyaml>=6.0.3` and `pyyaml==6.0.3 has no
usable wheels`. With verbose output, uv selects
`libcst-1.9.0-cp315-cp315-macosx_11_0_arm64.whl` as compatible. So LibCST
itself is not a 3.15 blocker; the older 0.3.0 result was backtracking forced by
PyYAML having no wheel. No uv environment variables or config files
(`uv.toml`, `pyproject.toml`, `~/.config/uv/uv.toml`) were found that alter
resolution.

Single root cause for the binary-only Airflow/LibCST failures: **PyYAML 6.0.3
is published only as a source distribution** (no cp315 wheel).

**PySpark 4.2.0.** JDK present (Homebrew OpenJDK 21.0.13). Isolated install
exit 0; import and `SparkSession` startup succeeded on Python 3.15.1. The
DataFrame job then failed with `PYTHON_VERSION_MISMATCH`: Spark's Python worker
ran Python 3.14 while the driver ran 3.15, because `PYSPARK_PYTHON` was not
set and a Python 3.14 interpreter was found first on PATH. This is a test-setup
error; the job has not yet run with a 3.15.1 worker, so PySpark is not
validated.

### PySpark and Airflow results (14:49–14:50 EDT)

**PySpark 4.2.0** (isolated env, JDK Homebrew OpenJDK 21.0.13, local mode,
`PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` set to the 3.15.1 env):

| Check | Result |
|---|---|
| DataFrame count | PASS |
| Aggregation (sum) | PASS |
| Python UDF executed on the worker | PASS |
| Worker interpreter version (`sys.version` from an RDD map) == 3.15.1 | PASS |
| `uv pip check` (isolated env) | PASS |

Limits: `local[1]` only; PyArrow and pandas were not installed in that env, so
Arrow-optimized UDFs and pandas-on-Spark were not tested (Spark logged that it
fell back to non-Arrow UDFs); no cluster mode.

**Apache Airflow 3.3.2** (isolated env, source builds allowed):

| Check | Result |
|---|---|
| Install | exit 0 — 129 packages resolved and installed |
| `uv pip check` | PASS — 129 packages compatible |
| `import airflow` on Python 3.15.1 | PASS (3.3.2) |
| `airflow db migrate` (temporary SQLite `AIRFLOW_HOME`) | exit 0 |
| `airflow dags list` | exit 0 (no DAGs; graphviz warning only) |

The install ran twice (two temp envs) with the same result. No `Built` lines
appeared, probably because the earlier source-built PyYAML wheel was in the uv
cache; this run therefore does not show whether a source build is needed from a
cold cache. Not tested: scheduler, api-server, DAG execution, executors,
providers.

**Repository side effect to review.** The MLflow probes run with a SQLite
backend in `/tmp` but MLflow's default artifact root is `./mlruns` relative to
the working directory, which was the repository. This created an untracked,
non-ignored `mlruns/` directory (44 KB; model files under `mlruns/2/`,
JSON artifacts under `mlruns/1/` and `mlruns/2/`). It is not part of the
project and was not committed or removed.

## Proposed Status Changes (not applied)

| Package | Current | Proposed | Rationale |
|---|---|---|---|
| prefect | SKIP | PASS (caveat: EventsWorker errors, reproduced on 3.14.10) | Functional checks passed; anomaly is not specific to 3.15.1 |
| mlflow | SKIP | BLOCKED for stock `mlflow`; `mlflow-skinny` PASS (core tracking); full install works only with a `pyarrow>=26` override | Upstream pin `pyarrow<26` plus no cp315 wheel for 25.x; override passes core, sklearn, dataset and table probes but fails `uv pip check` |
| pyspark | SKIP | PASS (local mode; no Arrow/pandas, no cluster) | Install, DataFrame ops, Python UDF and worker version 3.15.1 verified |
| apache-airflow | SKIP | PASS (provisional: install, import, DB migrate only) or hold SKIP until a DAG run is tested | Installs with source builds allowed; binary-only blocker is PyYAML (sdist-only). Scheduler and DAG execution untested |
| ray | BLOCKED | BLOCKED | No new validation |

Score under the repository formula
`round(100 * (PASS + 0.5 * BLOCKED + 0.25 * INCOMPAT) / (TOTAL - SKIP))`:

| Scenario | PASS | BLOCKED | SKIP | Score |
|---|---:|---:|---:|---:|
| Current reconciliation | 12 | 1 | 4 | 96% |
| Prefect -> PASS only | 13 | 1 | 3 | 96% |
| Prefect -> PASS, MLflow -> BLOCKED | 13 | 2 | 2 | 93% |
| MLflow -> BLOCKED only | 12 | 2 | 3 | 93% |
| Prefect -> PASS, MLflow -> PASS (override accepted) | 14 | 1 | 2 | 97% |
| Prefect, PySpark, Airflow -> PASS; MLflow -> BLOCKED | 15 | 2 | 0 | 94% |
| Prefect, PySpark, Airflow, MLflow -> PASS (override accepted) | 16 | 1 | 0 | 97% |
| Prefect, PySpark -> PASS; Airflow held SKIP; MLflow -> BLOCKED | 14 | 2 | 1 | 94% |

Recommended: Prefect -> PASS with the EventsWorker caveat recorded, since
the control run shows the behavior is not specific to Python 3.15.1.
Reclassifying MLflow from SKIP to BLOCKED is a methodology decision for the
owner. Prefect -> PASS alone leaves the score at 96%; with MLflow -> BLOCKED
it is 93%.

## Limitations

- Evidence is terminal output supplied by the tester; this report's
  author did not execute the tests.
- Temporary environments live under `/var/folders/.../T/` and may be removed.
- Source-build outcomes depend on local toolchain state.
- The score is a weighted package-compatibility indicator, not production readiness.
- Historical baseline (17%) and the 96% reconciliation were not modified.

## Recommended Follow-Up

1. Optional: capture the EventsWorker exception (e.g. run against a dedicated `prefect server start` instead of the ephemeral server) to confirm the root cause.
2. Re-run the skinny probe with `MLFLOW_ALLOW_FILE_STORE=true`. (sklearn log/load and dataset logging already pass on the override env.)
3. Decide MLflow/Prefect statuses, then update the readiness matrix.
4. Optional: run a trivial Airflow DAG (`airflow dags test`) and a PySpark job with PyArrow/pandas installed before treating those as more than provisional.
5. Decide what to do with the untracked `mlruns/` directory and consider ignoring it.
