# Python 3.15 Data Engineering Lab

**Author:** Dr. Ceasar Jackson Jr.
**Platform:** macOS 26.5 ARM64
**Environment Manager:** uv
**Project Location:** `~/Projects/python315_test`

## Executive Summary

This project began as a validation effort to evaluate Python 3.15 Beta for Data Engineering, Analytics, and Scientific Computing workloads.

Key findings:

- Python 3.15 beta environment successfully validated.
- NumPy, Pandas, Polars, DuckDB, SQLAlchemy, Pydantic, Plotly, Matplotlib, and JupyterLab are operational.
- Apache PyArrow currently lacks practical support for Python 3.15 beta in this environment.
- A Docker-based Python 3.14 + PyArrow environment was successfully implemented.

## Phase 1 – Python 3.15 Validation

### Environment

- Python 3.15.0b1
- uv package manager
- macOS 26.5 ARM64
- Virtual environment (.venv)

### Development Tools

- pytest
- ruff
- black
- mypy
- rich
- requests
- packaging
- wheel

## Phase 2 – Data Engineering Lite Stack

Installed and validated:

- numpy 2.4.6
- pandas 3.0.3
- polars 1.41.2
- duckdb 1.5.3
- sqlalchemy
- pydantic
- matplotlib
- plotly
- tqdm

## Phase 3 – Jupyter Ecosystem

Installed:

- jupyter
- jupyterlab
- notebook
- ipykernel
- ipywidgets

Validated:

- JupyterLab 4.5.7
- Notebook 7.5.6
- IPyKernel 7.2.0

Kernel:

- Python 3.15 DataEng

## Phase 4 – PyArrow Investigation

Result:

- PyArrow installation failed under Python 3.15 beta.

Root causes:

- Missing prebuilt wheels
- Rust compiler requirements
- Source-build dependency chain

Conclusion:

PyArrow is not yet ready for practical Python 3.15 beta usage.

## Phase 5 – Docker-Based PyArrow Environment

Docker image:

`pyarrow-dataeng:py314`

Base image:

`python:3.14-slim`

Installed:

- PyArrow
- DuckDB
- Pandas
- Polars
- NumPy
- JupyterLab
- Plotly
- Matplotlib

Results:

- Docker image built successfully
- JupyterLab launched successfully
- Port 8888 exposed successfully

## Recommended Next Steps

1. Build a Python 3.15 compatibility matrix.
2. Test PySpark, Delta Lake, Dask, Ray, MLflow, Prefect, and Airflow.
3. Benchmark Pandas vs Polars and DuckDB vs PyArrow.
4. Publish a formal Python 3.15 Data Engineering Readiness Assessment.

## Overall Assessment

| Area | Readiness |
|--------|--------|
| Python 3.15 Core Runtime | 95% |
| Data Engineering Stack | 90% |
| Jupyter Ecosystem | 100% |
| PyArrow Ecosystem | 30% |
| Docker Workaround | 100% |
| Production Readiness | 75% |

## Final Finding

Python 3.15 is already highly usable for modern Data Engineering workloads. Apache PyArrow remains the primary ecosystem blocker and is best isolated in a Python 3.14 Docker environment until official Python 3.15 support becomes available.
