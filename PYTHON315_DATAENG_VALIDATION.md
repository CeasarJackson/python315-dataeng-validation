# Python 3.15 Data Engineering Validation Suite

> **PROJECT STATUS:** COMPLETE
>
> Python 3.15 Data Engineering Validation Suite
> Phase 1–8 Complete
> Core Stack Validated
> Docker Workaround Validated
> Benchmarking Complete
> Readiness Assessment Published

**Author:** Dr. Ceasar Jackson Jr.
**Platform:** macOS 26.5 ARM64
**Environment Manager:** uv
**Project Location:** `~/Projects/python315_test`
**Python Version Tested:** 3.15.0b1
**Current Upstream Release:** Python 3.15.0b2
**Status:** Complete — All 8 Phases Finished

## Release Information

| Item | Value |
|--------|--------|
| Project | Python 3.15 Data Engineering Validation Suite |
| Version | 1.0.0 |
| Status | Complete |
| Validation Date | June 2026 |
| Python Tested | 3.15.0b1 |
| Current Upstream | 3.15.0b2 |
| Platform | macOS 26.5 ARM64 |
| Environment Manager | uv |

---

## Executive Summary

This project evaluates Python 3.15 Beta for modern Data Engineering workloads on Apple Silicon.

### Key Findings

- Core Data Engineering stack is operational.
- Jupyter ecosystem is fully functional.
- Polars consistently outperforms Pandas.
- DuckDB provides native high-performance Parquet support.
- PyArrow remains the primary ecosystem blocker.
- Docker-based mitigation successfully restores PyArrow-dependent workflows.
- Production deployment should wait until Python 3.15 General Availability (GA).

### Recommendation

Organizations may begin evaluating Python 3.15 for development and testing environments today while monitoring PyArrow compatibility and final GA stabilization.

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure and Directory Tree](#repository-structure-and-directory-tree)
3. [Environment Setup](#environment-setup)
4. [Validation Scripts](#validation-scripts)
5. [Notebooks](#notebooks)
6. [Phase Status](#phase-status)
7. [Logging Architecture](#logging-architecture)
8. [Running the Suite](#running-the-suite)
9. [Known Issues & Workarounds](#known-issues--workarounds)
10. [Benchmark Results](#benchmark-results)
11. [Readiness Assessment](#readiness-assessment)

---

## Overview

This repository contains the full validation suite for evaluating **Python 3.15 Beta** against modern Data Engineering, Analytics, and Scientific Computing workloads on macOS 26.5 ARM64. It spans eight phases — from environment bootstrap through extended ecosystem testing, formal benchmarking, and a published readiness assessment.

### Goals

- Confirm production-grade stability of the Python 3.15 core runtime on macOS ARM64.
- Validate the full data engineering toolchain: NumPy, Pandas, Polars, DuckDB, SQLAlchemy, Pydantic, Plotly, Matplotlib, JupyterLab.
- Document and isolate ecosystem blockers (primarily PyArrow) with a reproducible Docker workaround.
- Test extended stack packages: PySpark, Dask, Ray, MLflow, Prefect, Apache Airflow.
- Benchmark Pandas vs. Polars and DuckDB vs. PyArrow across dataset sizes.
- Produce and publish the formal Python 3.15 Data Engineering Readiness Assessment.

---
## Repository Structure and Directory Tree

```
python315_test/
├── README.md                                  # Project overview and quick-start
├── STATUS.md                                  # Current project status and validation log
├── ROADMAP.md                                 # Planned releases and milestones
├── PROJECT_STRUCTURE.md                       # Full directory reference
├── PORTFOLIO_SUMMARY.md                       # Portfolio-facing project summary
├── RELEASE_NOTES_v1.0.0.md                   # v1.0.0 release notes
├── PYTHON315_DATAENG_VALIDATION.md            # This document
├── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf # Formal Phase 8 assessment report
├── requirements-py315-dataeng-lite.txt
├── requirements-py315-dataeng-jupyter.txt
├── test_py315.py                              # Original pytest suite
├── data/                                      # Benchmark CSVs and generated charts
│   ├── benchmark_pandas_polars.csv
│   └── benchmark_duckdb_pyarrow.csv
├── docker_pyarrow_lab/
│   └── Dockerfile                           # Python 3.14 + OpenJDK 21 + PyArrow + PySpark
├── notebooks/
│   ├── 01_core_stack_validation.ipynb       # Phase 1 & 2 — runtime + stack smoke tests
│   ├── 02_benchmark_results.ipynb           # Phase 7 — benchmark charts and analysis
│   ├── 03_extended_stack_compatibility.ipynb # Phase 6 — compatibility matrix
│   └── 04_docker_pyarrow_py314_validation.ipynb # Phase 5 — Docker container validation
├── scripts/
│   ├── logger.py
│   ├── validate_core.py
│   ├── validate_stack.py
│   ├── validate_extended.py
│   ├── benchmark_pandas_polars.py
│   └── benchmark_duckdb_pyarrow.py
├── duckdb_tests/                              # DuckDB per-library validation suite
│   ├── test_duckdb_basic.py
│   ├── test_duckdb_pandas.py
│   ├── test_duckdb_native_parquet.py
│   ├── verify_duckdb_parquet.py
│   ├── benchmark_duckdb.py
│   ├── run_duckdb_validation.sh
│   ├── data/ + logs/
├── polars_tests/                              # Polars per-library validation suite
│   ├── test_polars_version.py
│   ├── test_polars_dataframe.py
│   ├── test_polars_groupby.py
│   ├── test_polars_join.py
│   ├── benchmark_polars.py
│   ├── run_polars_validation.sh
│   ├── data/ + logs/
├── sqlalchemy_tests/                          # SQLAlchemy per-library validation suite
│   ├── test_sqlalchemy_version.py
│   ├── test_sqlalchemy_core.py + orm + reflection + transactions
│   ├── benchmark_sqlalchemy.py
│   ├── run_sqlalchemy_validation.sh
│   ├── data/ + logs/
├── sqlite_tests/                              # SQLite per-library validation suite
│   ├── test_sqlite_version.py
│   ├── test_sqlite_crud.py + aggregate + file_db
│   ├── benchmark_sqlite.py
│   ├── run_sqlite_validation.sh
│   └── employees.db
├── pyarrow_tests/                             # Blocked — no cp315 wheels
│   ├── data/ + logs/
├── logs/
│   ├── validate_core.log + validate_stack.log + validate_extended.log
│   ├── benchmark_duckdb_pyarrow.log
│   └── pyarrow_failure_20260605.md
├── releases/
│   └── README.md
└── .venv/                                     # Python 3.15 virtual environment (uv-managed)
```

### Repository Notes

- The original exploratory notebook (`py315testing.ipynb`) has been retired.
- Validation activities are now organized into four dedicated notebooks.
- Docker is used to isolate PyArrow- and PySpark-dependent workloads.
- Benchmark outputs, logs, reports, and generated artifacts should be stored under `data/`, `logs/`, and `outputs/`.
- The readiness assessment PDF represents the final deliverable for Phase 8.
---

## Environment Setup

### Prerequisites

- macOS 26.5 (ARM64 / Apple Silicon)
- [uv](https://docs.astral.sh/uv/) package manager
- Docker Desktop (for PyArrow and PySpark isolation)
- Python 3.15.0b1 (installed via uv)

### Create and activate the environment

```bash
uv python install 3.15
cd ~/Projects/python315_test
uv venv --python 3.15
source .venv/bin/activate
```

### Install dependencies

```bash
uv pip install -r requirements-py315-dataeng-jupyter.txt
uv pip install colorlog dask prefect
```

### Build the Docker image

Provides Python 3.14 + OpenJDK 21 + PyArrow + PySpark for packages that cannot run
natively on Python 3.15 beta.

```bash
cd docker_pyarrow_lab
docker build -t pyarrow-dataeng:py314 .
cd ..
```



## Validation Scripts

Each script uses `scripts/logger.py` for colored terminal output (green INFO, yellow
WARNING, red ERROR, cyan DEBUG) and rotating log files under `logs/`.

| Script | Phase | Description |
|--------|-------|-------------|
| `logger.py` | — | Shared colored logging; 5 MB rotating file handler |
| `validate_core.py` | 1 | Python version, platform, venv, uv, dev tools |
| `validate_stack.py` | 2 | Import + functional smoke tests for all 9 core packages |
| `validate_extended.py` | 6 | Extended stack; PySpark via Docker; INCOMPAT detection |
| `benchmark_pandas_polars.py` | 7 | Pandas vs. Polars — 5 ops x 3 sizes x 3 runs |
| `benchmark_duckdb_pyarrow.py` | 7 | DuckDB vs. PyArrow — Parquet I/O + analytics |

---

## Notebooks

| Notebook | Phases | Description |
|----------|--------|-------------|
| `01_core_stack_validation.ipynb` | 1 & 2 | Interactive smoke tests for all 9 core packages with inline output and charts |
| `02_benchmark_results.ipynb` | 7 | Loads benchmark CSVs; generates Polars heatmap, absolute timings, DuckDB/PyArrow log-scale and signed speedup charts |
| `03_extended_stack_compatibility.ipynb` | 6 | Compatibility matrix visualisation, PyArrow failure demo, Prefect stdlib breakage, Dask partial compat, Docker smoke test |
| `04_docker_pyarrow_py314_validation.ipynb` | 5 | Confirms PyArrow 24.0.0 + DuckDB 1.5.3 + Pandas 3.0.3 inside Docker py314 (Python 3.14.5) |

---

## Phase Status

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| 1 | Python 3.15 runtime validation | ✅ Complete | 3.15.0b1 — macOS ARM64 |
| 2 | Data engineering lite stack | ✅ Complete | All 9 packages operational |
| 3 | Jupyter ecosystem | ✅ Complete | JupyterLab 4.5.7 validated |
| 4 | PyArrow investigation | ✅ Complete | No cp315 wheels; pkg_resources removed |
| 5 | Docker PyArrow workaround | ✅ Complete | pyarrow-dataeng:py314 — OpenJDK 21 |
| 6 | Extended stack | ✅ Complete | PySpark 4.1.2 PASS; 3 INCOMPAT; 2 SKIP |
| 7 | Benchmarks | ✅ Complete | CSVs + 4 charts in `data/` |
| 8 | Formal Readiness Assessment | ✅ Complete | `PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf` |

---

## Logging Architecture

| Level | Terminal Colour | Use |
|-------|----------------|-----|
| DEBUG | Cyan | Raw version strings, internal state |
| INFO | Green | Normal progress, `[PASS]` results |
| WARNING | Yellow | Soft failures, `[SKIP]`, `[INCOMPAT]` |
| ERROR | Red | Import failures, `[FAIL]` results |
| CRITICAL | Bold Red | Fatal conditions |

Log files: `logs/<script_name>.log` — 5 MB max, 3 backups.

---

## Quick Validation Commands

```bash
python --version
uv --version

pytest test_py315.py -v

jupyter lab

docker images | grep pyarrow-dataeng

python -c "import pandas, polars, duckdb; print('PASS')"
```

---

## Running the Suite

```bash
source .venv/bin/activate

python scripts/validate_core.py       # Phase 1
python scripts/validate_stack.py      # Phase 2
python scripts/validate_extended.py   # Phase 6 (requires Docker image)
python scripts/benchmark_pandas_polars.py   # Phase 7
python scripts/benchmark_duckdb_pyarrow.py  # Phase 7 (requires Docker image)

pytest test_py315.py -v --tb=short

# JupyterLab with PyArrow + PySpark (Docker)
docker run -p 8888:8888 pyarrow-dataeng:py314
# -> http://localhost:8888

# PySpark shell
docker run --rm -it pyarrow-dataeng:py314 pyspark
```

---

## Known Issues & Workarounds

### PyArrow — no Python 3.15 cp315 wheels

**Root cause:** No prebuilt cp315 wheels on PyPI. Source build fails: Rust + C++
toolchain required; `pkg_resources` (removed in Python 3.15) referenced in legacy
`setup.py`.

**Cascade:** Blocks dask.dataframe, Delta Lake, MLflow >= 2.17.

**Workaround:** `pyarrow-dataeng:py314` Docker image. DuckDB substitutes for PyArrow in
the majority of Parquet I/O use cases natively on Python 3.15.

**Track:** https://github.com/apache/arrow

### Prefect 3.7.x — stdlib breaking change

**Root cause:** `typing.no_type_check_decorator` removed in Python 3.15 (deprecated
3.13, removed per PEP 749). Prefect imports it at startup.

**Workaround:** None until upstream patches.
**Track:** https://github.com/PrefectHQ/prefect

### PySpark — JDK required

**Workaround:** `pyarrow-dataeng:py314` includes OpenJDK 21. PySpark 4.1.2 validated
via Docker. `validate_extended.py` handles this transparently.

**Note:** `python:3.14-slim` (Debian Trixie) dropped OpenJDK 17. Dockerfile uses
`openjdk-21-jre-headless` — fully supported by PySpark 3.x and 4.x.

---

## Benchmark Results

### Pandas vs. Polars — Python 3.15 native

Polars is faster than Pandas on **all operations at all dataset sizes**.

| Operation | 100K | 1M | 5M |
|-----------|------|----|----|
| Creation | 6.1x | 5.7x | 5.3x |
| Filter | 2.0x | 3.1x | 1.9x |
| Groupby | 4.7x | 19.6x | **39.7x** |
| Sort | 5.5x | 6.3x | 6.8x |
| Join | 1.2x | 3.5x | 5.3x |

### DuckDB vs. PyArrow — DuckDB native · PyArrow via Docker py314

| Operation | 5M DuckDB | 5M PyArrow | Winner |
|-----------|-----------|-----------|--------|
| Parquet write | 0.056s | 0.296s | DuckDB 5.3x |
| Parquet read | 0.005s | 0.057s | DuckDB 12.3x |
| Filter | 0.931s | 0.025s | PyArrow 37x |
| Aggregation | 0.006s | 0.008s | DuckDB 1.3x |
| Join | 2.470s | 0.032s | **PyArrow 77x** |

**Recommendation:** DuckDB for Parquet I/O and SQL analytics natively on Python 3.15.
Docker py314 for filter/join-heavy in-memory operations.

---

## Readiness Assessment

| Area | Readiness | Notes |
|------|-----------|-------|
| Python 3.15 Core Runtime | 95% | Stable beta; beta-level rough edges in C-extensions |
| Data Engineering Stack | 90% | All 9 core packages pass full smoke tests |
| Jupyter Ecosystem | 100% | JupyterLab 4.5.7 + Python 3.15 DataEng kernel |
| PyArrow Ecosystem | 30% | Blocked; Docker workaround fully mitigates |
| Extended Stack | 50% | PySpark PASS via Docker; Dask/MLflow/Prefect INCOMPAT |
| Docker Workaround | 100% | PyArrow + PySpark + OpenJDK 21 fully functional |
| Production Readiness | 75% | Not for production until GA; core stack is production-grade |

### Final Finding

Python 3.15 is **already highly usable** for modern Data Engineering workloads. The core
runtime, primary analytical libraries, and the full Jupyter ecosystem are operational and
stable on macOS ARM64. Polars is 39.7x faster than Pandas at groupby (5M rows). DuckDB
provides fast native Parquet I/O without PyArrow. PySpark 4.1.2 is validated via Docker.

PyArrow remains the primary ecosystem blocker until cp315 wheels are published. Prefect
3.7.x is blocked by a Python 3.15 stdlib breaking change. The remaining 25% gap to
production readiness reflects the beta status of the runtime, not the data engineering
toolchain.

## Future Work

- Retest PyArrow when cp315 wheels become available.
- Retest Dask DataFrame compatibility.
- Retest MLflow compatibility.
- Retest Prefect after Python 3.15 fixes are released.
- Validate Apache Airflow.
- Repeat benchmarks against Python 3.15 RC1.
- Publish v1.0 GitHub release package.

---

*Dr. Ceasar Jackson Jr. — Python 3.15 Data Engineering Validation Suite — June 2026*
