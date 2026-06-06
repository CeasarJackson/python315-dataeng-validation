# Project Structure

**Version:** 1.0.0
**Updated:** June 2026

---

## Directory Tree

```
python315_test/
├── README.md                                  # Project overview and quick-start
├── STATUS.md                                  # Current project status and validation log
├── ROADMAP.md                                 # Planned releases and milestones
├── PROJECT_STRUCTURE.md                       # This document
├── PORTFOLIO_SUMMARY.md                       # Portfolio-facing project summary
├── RELEASE_NOTES_v1.0.0.md                   # v1.0.0 release notes
├── PYTHON315_DATAENG_VALIDATION.md            # Full validation suite reference
├── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf # Formal Phase 8 assessment report
├── requirements-py315-dataeng-lite.txt        # Minimal requirements
├── requirements-py315-dataeng-jupyter.txt     # Full stack + Jupyter requirements
├── test_py315.py                              # Original pytest suite
├── data/                                      # Benchmark CSVs and chart outputs
│   ├── benchmark_pandas_polars.csv
│   └── benchmark_duckdb_pyarrow.csv
├── docker_pyarrow_lab/
│   └── Dockerfile                           # Python 3.14 + OpenJDK 21 + PyArrow + PySpark
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
│   └── benchmark_duckdb_pyarrow.py
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
├── logs/                                      # Execution logs and failure reports
│   ├── validate_core.log
│   ├── validate_stack.log
│   ├── validate_extended.log
│   ├── benchmark_duckdb_pyarrow.log
│   └── pyarrow_failure_20260605.md
├── releases/
│   └── README.md                            # Release artifact location and tag index
└── .venv/                                     # Python 3.15 virtual environment (uv-managed)
```

---

## Directory Purpose

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Phase-level validation and benchmark runners using shared logger |
| `notebooks/` | Interactive Jupyter validation notebooks with inline output |
| `duckdb_tests/` | DuckDB standalone test suite: SQL, Pandas integration, native Parquet |
| `polars_tests/` | Polars standalone test suite: DataFrame, groupby, join |
| `sqlalchemy_tests/` | SQLAlchemy standalone test suite: core, ORM, reflection, transactions |
| `sqlite_tests/` | SQLite standalone test suite: CRUD, aggregation, file DB |
| `pyarrow_tests/` | PyArrow test suite — currently empty pending cp315 wheel availability |
| `airflow_tests/` | Airflow 3.x per-library validation suite: DAG, operators, models, benchmark |
| `docker_pyarrow_lab/` | Dockerfile for Python 3.14 + OpenJDK 21 + PyArrow + PySpark isolation layer |
| `data/` | Benchmark CSVs and chart PNGs generated by Phase 7 |
| `logs/` | Rotating execution logs and dated failure reports |
| `releases/` | Release index; archives stored at `~/Local_Backups/python315_releases/` |

---

## Test Suite Conventions

Each per-library test suite (`*_tests/`) follows the same pattern:

- `test_<lib>_version.py` — import and version smoke test
- `test_<lib>_<feature>.py` — targeted functional tests
- `benchmark_<lib>.py` — timing benchmark
- `run_<lib>_validation.sh` — shell runner that executes all tests in order
- `data/` — test fixtures and generated output
- `logs/` — per-suite execution logs

---

*Dr. Ceasar Jackson Jr. — Python 3.15 Data Engineering Validation Suite — June 2026*
