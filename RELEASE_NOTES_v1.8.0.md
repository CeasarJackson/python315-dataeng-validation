

# Release Notes – v1.8.0

## Release Date
June 2026

## Overview
Version 1.8.0 introduces automated release packaging, unified validation execution, enhanced Python 3.15 compatibility reporting, and standardized release artifacts for the Python 3.15 Data Engineering Validation Lab.

## Validation Results

### Automated Test Suites
- SQLite: 11/11 Passed
- SQLAlchemy: 11/11 Passed
- DuckDB: 8/8 Passed
- Polars: 11/11 Passed
- Apache Airflow: 14/14 Passed

### Total Status
- All validation suites completed successfully under Python 3.15.0b2.

## Compatibility Summary

| Component | Status |
|------------|--------|
| NumPy | PASS |
| Pandas | PASS |
| Polars | PASS |
| DuckDB | PASS |
| SQLAlchemy | PASS |
| Pydantic | PASS |
| Matplotlib | PASS |
| Plotly | PASS |
| JupyterLab | PASS |
| SQLite3 | PASS |
| Prefect | PASS |
| MLflow | PASS |
| Airflow | PASS |
| PyArrow | BLOCKED |
| Ray | BLOCKED |
| Dask DataFrame | INCOMPAT |
| PySpark | SKIP |

Summary:
- PASS = 13
- FAIL = 0
- INCOMPAT = 1
- BLOCKED = 2
- SKIP = 1

## Major Enhancements

### Unified Validation Runner
Added `scripts/validate_all.sh` to execute all validation suites from a single command.

### Release Automation
Added automated release workflow through `scripts/release.sh`.

### Report Generation
Automated creation of:
- Compatibility reports
- Manifest metadata
- Readiness assessments
- PDF reports

### Packaging
Automated creation of:
- Versioned release archives
- SHA256 checksum files
- Release-ready artifacts

## Known Limitations

### PyArrow
CPython 3.15 wheels are not yet available.

### Ray
Python 3.15 support remains unavailable.

### Dask
Blocked by PyArrow dependency chain.

### PySpark
Docker validation image unavailable during testing.

## Production Readiness

Recommended for:
- Data engineering experimentation
- Analytics workloads
- DuckDB development
- Polars pipelines
- SQLAlchemy validation
- Airflow compatibility testing

Not recommended for:
- Production PyArrow workloads
- Production Ray deployments
- Production Dask workloads

## Release Artifacts
- Compatibility Report
- Manifest Metadata
- PDF Readiness Assessment
- Validation Logs
- Release Archive
- SHA256 Checksum

## Next Steps
- Validate PyArrow when Python 3.15 wheels become available.
- Re-test Dask ecosystem compatibility.
- Validate Ray support.
- Continue Python 3.15 release-candidate testing.
- Prepare for Python 3.15 GA certification.

## Final Status
Version 1.8.0 establishes the first fully automated release and validation workflow for the Python 3.15 Data Engineering Validation Lab.