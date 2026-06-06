# Release Notes — v1.4.0

**Python 3.15 Data Engineering Validation Suite**
**Release Date:** June 2026
**Author:** Dr. Ceasar Jackson Jr.

## Summary

Pre-GA baseline established. All validatable packages are confirmed
PASS. Only upstream-blocked packages (PyArrow, Ray) remain — no code
defects detected in any tested package.

## Results at v1.4.0

| Metric | Value |
|--------|-------|
| PASS | 14 |
| INCOMPAT | 1 (dask.dataframe — pyarrow dep) |
| BLOCKED | 2 (pyarrow, ray — no cp315 wheels) |
| FAIL | 0 |
| Production Readiness | 85% |

## Improvements since v1.0.0

| Package | v1.0.0 | v1.4.0 |
|---------|--------|--------|
| prefect 3.7.3 | INCOMPAT | PASS |
| mlflow 2.16.2 | INCOMPAT | PASS |
| apache-airflow 3.2.2 | SKIP | PASS |
| pyspark 4.1.2 | SKIP | PASS (via Docker) |

## Validation Suite

- 6 per-library test suites: duckdb, polars, sqlalchemy, sqlite, airflow, pyarrow
- Automated report generation: `scripts/generate_report.py`
- Cycle comparison: `scripts/compare_reports.py`
- 4 versioned reports: 3.15.0b1 through 3.15.0rc2

## Next: v2.0.0

Triggered when PyArrow publishes cp315 wheels:
```zsh
uv pip install pyarrow
.venv/bin/python scripts/generate_report.py --release 3.15.0ga --auto-commit
.venv/bin/python scripts/compare_reports.py 3.15.0rc2 3.15.0ga
git tag v2.0.0 -m "v2.0.0: Python 3.15 GA production assessment"
git push origin main --tags
```
