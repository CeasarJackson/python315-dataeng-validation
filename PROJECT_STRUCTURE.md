# Project Structure

**Version:** 1.9.1
**Updated:** June 2026 (Release Automation Edition)

---

## Directory Tree

```
python315_test/
├── README.md                                  # Project overview and quick-start
├── STATUS.md                                  # Current project status and validation log
├── ROADMAP.md                                 # Planned releases and milestones
├── PROJECT_STRUCTURE.md                       # This document
├── PORTFOLIO_SUMMARY.md                       # Portfolio-facing project summary
├── RELEASE_NOTES_v1.0.0.md                   # Initial release notes
├── RELEASE_NOTES_v1.4.0.md                   # Airflow validation release
├── PYTHON315_DATAENG_VALIDATION.md            # Full validation suite reference
├── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf # Formal Phase 8 assessment report
├── pytest.ini                                # Centralized pytest configuration
├── requirements-py315-dataeng-lite.txt        # Minimal requirements
├── requirements-py315-dataeng-jupyter.txt     # Full stack + Jupyter requirements
├── test_py315.py                              # Original pytest suite
├── data/                                      # Benchmark CSVs and chart outputs
│   ├── benchmark_pandas_polars.csv
│   └── benchmark_duckdb_pyarrow.csv
├── docker/
│   └── pyarrow_lab/
│       └── Dockerfile                       # Python 3.14 + OpenJDK 21 + PyArrow + PySpark
├── docker_pyarrow_lab/
│   └── Dockerfile                           # Legacy Docker validation environment
├── notebooks/
│   ├── 01_core_stack_validation.ipynb       # Phase 1 & 2 — runtime + stack smoke tests
│   ├── 02_benchmark_results.ipynb           # Phase 7 — benchmark charts and analysis
│   ├── 03_extended_stack_compatibility.ipynb # Phase 6 — compatibility matrix
│   └── 04_docker_pyarrow_py314_validation.ipynb # Phase 5 — Docker container validation
├── scripts/                                   # Automated validation and benchmark runners
│   ├── logger.py
│   ├── validate_core.py
│   ├── validate_stack.py
│   ├── validate_extended.py
│   ├── benchmark_pandas_polars.py
│   ├── benchmark_duckdb_pyarrow.py
│   ├── validate_all.sh                           # Unified validation runner
│   ├── release.sh                                # Automated release builder
│   ├── generate_report.py                        # Compatibility report generator
│   └── compare_reports.py                        # Historical report comparison utility
├── duckdb_tests/                              # DuckDB per-library validation suite
│   ├── test_duckdb_basic.py
│   ├── test_duckdb_pandas.py
│   ├── test_duckdb_native_parquet.py
│   ├── verify_duckdb_parquet.py
│   ├── benchmark_duckdb.py
│   ├── run_duckdb_validation.sh
│   ├── data/
│   └── logs/
├── polars_tests/                              # Polars per-library validation suite
│   ├── test_polars_version.py
│   ├── test_polars_dataframe.py
│   ├── test_polars_groupby.py
│   ├── test_polars_join.py
│   ├── benchmark_polars.py
│   ├── run_polars_validation.sh
│   ├── data/
│   └── logs/
├── sqlalchemy_tests/                          # SQLAlchemy per-library validation suite
│   ├── test_sqlalchemy_version.py
│   ├── test_sqlalchemy_core.py
│   ├── test_sqlalchemy_orm.py
│   ├── test_sqlalchemy_reflection.py
│   ├── test_sqlalchemy_transactions.py
│   ├── benchmark_sqlalchemy.py
│   ├── run_sqlalchemy_validation.sh
│   ├── data/
│   └── logs/
├── sqlite_tests/                              # SQLite per-library validation suite
│   ├── test_sqlite_version.py
│   ├── test_sqlite_crud.py
│   ├── test_sqlite_aggregate.py
│   ├── test_sqlite_file_db.py
│   ├── benchmark_sqlite.py
│   ├── run_sqlite_validation.sh
│   └── employees.db
├── pyarrow_tests/                             # PyArrow validation suite (blocked — no cp315 wheels)
│   ├── data/
│   └── logs/
├── airflow_tests/                             # Airflow 3.x per-library validation suite
│   ├── test_airflow_version.py
│   ├── test_airflow_dag.py
│   ├── test_airflow_models.py
│   ├── test_airflow_deprecated_apis.py
│   ├── benchmark_airflow.py
│   ├── run_airflow_validation.sh
│   ├── data/
│   └── logs/
├── logs/                                      # Execution logs and failure reports
│   ├── validate_core.log
│   ├── validate_stack.log
│   ├── validate_extended.log
│   ├── benchmark_duckdb_pyarrow.log
│   └── pyarrow_failure_20260605.md
├── reports/
│   ├── README.md
│   ├── template/
│   ├── 3.15.0b1/
│   ├── 3.15.0b2/
│   ├── 3.15.0b2/readiness_matrix.json            # Readiness synchronization source
│   ├── 3.15.0rc1/
│   ├── 3.15.0rc2/
│   ├── 3.15.0/                       # GA (pending; see docs/runbooks)
│   ├── v1.8.0/
│   └── v1.8.1/
├── tools/
│   ├── add_standard_headers.py              # Repository-wide standards enforcement
│   ├── build_reports_system.py              # Report framework builder
│   ├── sync_readiness.py                    # Readiness report synchronization utility
│   ├── update_docs.py                       # Documentation synchronization
│   └── fix_repo_docs.py                     # Repository documentation repair utility
├── releases/
│   └── README.md                            # Release artifact location and tag index
└── .venv/                                     # Python 3.15 virtual environment (uv-managed)
```

---

## Directory Purpose

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Validation runners, report generation, release automation, and benchmarking |
| `notebooks/` | Interactive Jupyter validation notebooks with inline output |
| `duckdb_tests/` | DuckDB standalone test suite: SQL, Pandas integration, native Parquet |
| `polars_tests/` | Polars standalone test suite: DataFrame, groupby, join |
| `sqlalchemy_tests/` | SQLAlchemy standalone test suite: core, ORM, reflection, transactions |
| `sqlite_tests/` | SQLite standalone test suite: CRUD, aggregation, file DB |
| `pyarrow_tests/` | PyArrow test suite — currently empty pending cp315 wheel availability |
| `airflow_tests/` | Airflow 3.x per-library validation suite: DAG, operators, models, benchmark |
| `docker/pyarrow_lab/` | Primary Docker validation environment for PyArrow and PySpark compatibility testing |
| `docker_pyarrow_lab/` | Legacy Docker validation environment retained for backward compatibility |
| `data/` | Benchmark CSVs and chart PNGs generated by Phase 7 |
| `logs/` | Rotating execution logs and dated failure reports |
| `reports/` | Versioned readiness assessments, compatibility reports, manifests, and PDFs |
| `tools/` | Repository maintenance and report-system automation utilities |
| `releases/` | Release index; archives stored at `~/Local_Backups/python315_releases/` |

---

## Validation Architecture

The repository now uses a layered validation model:

### Layer 1 — Library Validation

- SQLite
- SQLAlchemy
- DuckDB
- Polars
- Apache Airflow
- PyArrow (blocked pending cp315 wheel availability)

### Layer 2 — Stack Validation

- validate_core.py
- validate_stack.py
- validate_extended.py

### Layer 3 — Unified Validation

- validate_all.sh

Executes all validation suites and produces consolidated logging.

### Layer 4 — Reporting

- generate_report.py
- compare_reports.py

Produces:

- Compatibility Reports
- Executive Summaries
- Full Readiness Assessments
- Readiness Matrices (Markdown + JSON)
- Assessment PDFs
- Release Manifests
- Readiness Synchronization Validation

### Layer 5 — Release Automation

- release.sh

Produces:

- Versioned release archives
- SHA256 checksums
- Historical report snapshots
- Release manifests

---

*Dr. Ceasar Jackson Jr. — Python 3.15 Compatibility & Readiness Assessment Platform — Version 1.9.1*
