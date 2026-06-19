# Python 3.15 Compatibility Findings

**Project:** Python 3.15 Compatibility Validation Lab  
**Author:** Dr. Ceasar Jackson Jr.  
**Date:** 2026-06-19

---

# Executive Summary

This project evaluates Python 3.15 compatibility across a modern Data Engineering,
Analytics, Visualization, Workflow Orchestration, and Data Science stack.

Testing was performed using Python 3.15.0b2 on macOS ARM64 using uv-managed
virtual environments.

The majority of the core Data Engineering ecosystem is already functioning
correctly on Python 3.15. However, several critical packages remain blocked
by upstream compatibility issues.

---

# Test Environment

| Component | Value |
|------------|---------|
| Platform | macOS ARM64 |
| OS | macOS Tahoe |
| Python | 3.15.0b2 |
| Package Manager | uv |
| Compiler | Apple Clang 21 |
| Fortran | GCC/GFortran 16.1.0 |
| OpenBLAS | 0.3.33 |
| CMake | 4.3.4 |

---

# Core Data Engineering Stack

| Package | Version | Status |
|----------|----------|----------|
| NumPy | 2.4.6 | PASS |
| Pandas | 3.0.3 | PASS |
| Polars | 1.41.2 | PASS |
| DuckDB | 1.5.3 | PASS |
| SQLAlchemy | 2.0.50 | PASS |
| Pydantic | 2.13.4 | PASS |
| Matplotlib | 3.10.9 | PASS |
| Plotly | 6.7.0 | PASS |
| JupyterLab | 4.5.7 | PASS |
| SQLite3 | 3.53.1 | PASS |

---

# Workflow & Platform Stack

| Package | Status |
|----------|----------|
| Airflow 3.2.2 | PASS |
| MLflow 2.16.2 | PASS |
| Prefect | FAIL |
| Dask | FAIL |
| Ray | SKIP |
| Delta Lake | SKIP |
| PySpark | SKIP |

---

# Major Findings

## Finding 1 – SciPy

### Status

INCOMPATIBLE

### Summary

SciPy 1.17.1 cannot currently be installed successfully on Python 3.15.

No cp315 binary wheel exists.

Installation falls back to source compilation.

Compilation proceeds successfully through:

- OpenBLAS discovery
- NumPy integration
- CMake detection
- GFortran detection
- Meson configuration
- Ninja build generation

The build ultimately fails during Pythran code generation.

### Error

```text
TypeError:
ast.Compare.__init__ missing 1 required positional argument: 'left'