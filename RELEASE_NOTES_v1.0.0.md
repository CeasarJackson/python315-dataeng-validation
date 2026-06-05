# Release Notes — v1.0.0

**Project:** Python 3.15 Data Engineering Validation Suite
**Version:** 1.0.0
**Release Date:** June 2026
**Author:** Dr. Ceasar Jackson Jr.

---

## Summary

Initial release of the Python 3.15 Data Engineering Validation Suite.
This release covers all eight validation phases and establishes the
baseline compatibility report for Python 3.15.0b1 on macOS 26.5 ARM64.

---

## What's Included

### Validation Coverage

| Area | Result |
|------|--------|
| Python 3.15 Core Runtime | PASS — 95% readiness |
| Data Engineering Stack (9 packages) | PASS — 90% readiness |
| Jupyter Ecosystem | PASS — 100% readiness |
| PyArrow | FAIL — no cp315 wheels |
| PySpark 4.1.2 | PASS — via Docker py314 + OpenJDK 21 |
| Dask.dataframe | INCOMPAT — pyarrow runtime dep |
| Prefect 3.7.x | INCOMPAT — stdlib breaking change |
| MLflow | INCOMPAT — pyarrow hard dep |
| SQLite 3.50.4 | PASS |
| DuckDB Native Parquet | PASS |
| SQLAlchemy 2.0.50 | PASS |
| Production Readiness | 75% |

### Per-Library Test Suites Added

- `duckdb_tests/` — basic SQL, Pandas integration, native Parquet I/O, benchmark
- `polars_tests/` — DataFrame creation, groupby, join, version validation
- `sqlalchemy_tests/` — core, ORM, reflection, transactions, benchmark
- `sqlite_tests/` — CRUD, aggregation, file DB, version detection, benchmark

### Benchmark Results

- Polars 39.7x faster than Pandas at groupby (5M rows)
- DuckDB 12.3x faster Parquet read vs PyArrow at 5M rows
- PyArrow 77x faster hash join at 5M rows (via Docker)

### Documentation

- `PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf` — formal 11-page assessment
- `PYTHON315_DATAENG_VALIDATION.md` — full validation suite reference
- `STATUS.md`, `ROADMAP.md`, `PORTFOLIO_SUMMARY.md` — project governance

---

## Known Issues

### PyArrow — no cp315 wheels

No prebuilt cp315 wheels on PyPI. Source build fails at CMake configuration
(`ArrowConfig.cmake not found`). Blocks dask.dataframe, Delta Lake, MLflow >= 2.17.
**Workaround:** `pyarrow-dataeng:py314` Docker image.

### Prefect 3.7.x — stdlib breakage

`typing.no_type_check_decorator` removed in Python 3.15 per PEP 749.
Prefect imports it at startup. No workaround until upstream patch.

### fastparquet / cramjam

PyO3 0.25 supports Python <= 3.14. Affects fastparquet dependency chain.
DuckDB native Parquet is the recommended substitute.

---

## Release Artifacts

Release archives are stored outside Git at:
`~/Local_Backups/python315_releases/python315_dataeng_validation_v1.0.0.zip`

### Packaging Exclusions

```
.venv/*
__pycache__/*
*.pyc
.git/*
logs/*
*.db
```

---

## Next Release: v1.1.0

- Apache Airflow validation
- Updated benchmarks
- Additional per-library test suites

See `ROADMAP.md` for the full release plan.
