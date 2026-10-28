# Python 3.15 Compatibility Matrix

> **Current evidence checkpoint (2026-10-28):** Python 3.15.2 remains **94% PROVISIONAL**, with 15 packages PASS and two BLOCKED (MLflow and Ray). PyArrow 26.0.0 and Dask DataFrame passed executed workloads. PySpark 4.2.0 passed Docker local-mode checks with Python 3.15.2, PyArrow 26.0.0 and pandas 3.1.0 on Linux ARM64; pandas 3.x support remains incomplete. The saved targeted-run transcript confirms 8/8 PASS; advanced 5/5 is conversation-reported. The release checklist records 331 passed, one skipped. See the [post-release evidence checkpoint](../docs/POST_RELEASE_EVIDENCE_2026-10-28.md) and [3.15.2 manifest](../reports/3.15.2/manifest.json).
>
> **Historical material below:** all earlier “current” labels, versions, scores, blockers, test counts, benchmarks and commands describe their original checkpoints. They are superseded for current status by the checkpoint above; `STATUS.md` still contains older status summaries. MLflow remains blocked by its `pyarrow<26` cap combined with missing cp315 wheels for eligible PyArrow versions; Ray lacked cp315 wheels on the configured index at the recorded check. Published v2.2.1 artifacts are unchanged.

> **Historical note (2026-10-02):** the results in this document were produced under Python 3.15.0b2, in an environment later found to be internally inconsistent (see `docs/KNOWN_ISSUES.md`). The latest validated release is 3.15.0rc2; current numbers live in `STATUS.md` and `reports/3.15.0rc2/manifest.json`.

Author: Dr. Ceasar Jackson Jr.

## Environment

| Component | Value |
|------------|------------|
| Python | 3.15.0b2 |
| Platform | macOS 26.5 ARM64 |
| Environment | uv-managed virtualenv |
| Validation Date | 2026-06-06 |
| Project Version | 1.8.1 |

---

## Core Data Engineering Stack

| Package | Version | Status |
|----------|----------|----------|
| NumPy | 2.4.6 | PASS |
| Pandas | 3.0.3 | PASS |
| Polars | 1.41.2 | PASS |
| DuckDB | 1.5.3 | PASS |
| SQLAlchemy | 2.0.50 | PASS |
| SQLite3 | 3.53.1 | PASS |
| Pydantic | 2.13.4 | PASS |
| Matplotlib | 3.10.9 | PASS |
| Plotly | 6.7.0 | PASS |
| JupyterLab | 4.5.7 | PASS |

---

## Workflow & Orchestration

| Package | Version | Status |
|----------|----------|----------|
| Apache Airflow | 3.2.2 | PASS |
| Prefect | 3.7.3 | PASS |

---

## Extended Ecosystem


| Package | Status | Notes |
|----------|----------|----------|
| PyArrow | BLOCKED | No cp315 wheels available |
| Dask DataFrame | INCOMPAT | Depends on PyArrow |
| Ray | BLOCKED | No cp315 wheels available |
| PySpark | SKIP | Docker validation pending |
| MLflow | PASS | Imports and validation successful |

---

## Validation Summary

| Result | Count |
|----------|----------|
| PASS | 13 |
| FAIL | 0 |
| INCOMPAT | 1 |
| BLOCKED | 2 |
| SKIP | 1 |

---

## Readiness Assessment

Current readiness for Python 3.15 adoption within a modern Data Engineering environment is estimated at 92%.

Remaining compatibility limitations are external ecosystem issues rather than project-level defects.

Primary blockers remain:

1. Apache PyArrow wheel availability.
2. Ray wheel availability.
3. PySpark validation image completion.

---

## Recommendation

Python 3.15.0b2 is suitable for:

- Development
- Testing
- Validation Labs
- Analytics Workloads
- Data Engineering Prototyping

Production deployment should continue monitoring PyArrow and Ray ecosystem support until General Availability readiness is confirmed.
