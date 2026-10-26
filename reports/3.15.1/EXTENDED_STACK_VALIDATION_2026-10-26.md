# Python 3.15.1 — Extended Stack Validation

**Author:** Ceasar Jackson
**Validation date:** 2026-10-26
**Report generated:** 2026-10-26 12:28:51 EDT
**Platform:** macOS arm64 (Apple Silicon)
**Interpreter:** CPython 3.15.1

## 1. Executive Summary

The tested Python 3.15.1 data-engineering and notebook workloads
completed successfully on macOS arm64.

This report supplements the original compatibility baseline.
It does not establish production readiness for the full ecosystem.

## 2. Validation Results

| Validation | Result |
|---|---|
| Core data-engineering stack | 11/11 PASS |
| PyYAML source-build tests | 5/5 PASS |
| JupyterLab/Dask integration | 7/7 PASS |
| Jupyter notebook execution | PASS |
| Dask DataFrame integration | 6/6 PASS |
| Explicit Jupyter kernel isolation | PASS |
| Integration dependency check | 101 packages compatible |
| Original core environment check | 25 packages compatible |
| Git diff integrity | PASS |

These results represent separate validation runs.

## 3. Core Stack

| Package | Version |
|---|---|
| NumPy | 2.5.4 |
| pandas | 3.1.0 |
| Polars | 1.41.2 |
| DuckDB | 2.0.0 |
| SQLAlchemy | 2.0.50 |
| Pydantic | 2.14.1 |
| Matplotlib | 3.11.2 |
| Plotly | 6.7.0 |
| PyArrow | 26.0.0 |

The core stack passed 11 functional checks.

Detailed evidence:
CORE_STACK_VALIDATION_2026-10-26.md

## 4. PyYAML

PyYAML 6.0.3 built successfully from source.
All five functional checks passed.

The installation reported yaml.__with_libyaml__ as False.
Therefore, the validated implementation was pure Python.

A compatible CPython 3.15 binary wheel was unavailable
under the tested binary-only installation policy.

The LibYAML C extension was not validated.

## 5. JupyterLab

JupyterLab 4.5.7 installed and imported successfully.

The notebook infrastructure executed Python 3.15.1
NumPy and Dask computations and produced the expected output.

A persistent JupyterLab web-server session was not tested.

## 6. Dask Array and Delayed

Dask 2026.7.1 passed array and delayed computations.

Array sum of integers 0 through 99: 4950.
Delayed sum of squares of integers 0 through 9: 285.

The initial Dask Array failure was caused by a missing
optional NumPy dependency in the isolated environment.

Installing the Dask Array dependency set resolved the issue.

## 7. Dask DataFrame

Dask DataFrame 2026.7.1 was validated with:

- pandas 3.1.0
- PyArrow 26.0.0
- NumPy 2.5.4

Six checks passed:

1. Package versions.
2. DataFrame partitioning.
3. DataFrame filtering.
4. GroupBy aggregation.
5. Parquet write/read round-trip.
6. PyArrow interoperability.

These tests used local partitions rather than a distributed cluster.

## 8. Kernel Isolation

The initial explicit kernel-isolation test failed because
the virtual-environment executable symlink was resolved
to the Homebrew interpreter.

The corrected kernelspec preserved the virtual-environment
Python executable path.

The corrected notebook verified Python 3.15.1, sys.prefix,
and a Dask computation producing 4950.

The corrected kernel-isolation test passed with exit code 0.

## 9. Transport Warning

Jupyter emitted a warning about unencrypted TCP transport.

The warning did not prevent local notebook execution.
Network exposure and production transport security
were not evaluated.

## 10. Environment Integrity

The isolated integration environment passed uv pip check
with 101 installed distributions.

The original .venv3151 environment passed uv pip check
with 25 installed distributions.

Git diff integrity checks passed.

Existing repository modifications were preserved.

## 11. Remaining Limitations

- PyYAML binary-wheel availability.
- LibYAML C-extension compatibility.
- Persistent JupyterLab server operation.
- Distributed Dask cluster execution.
- Production-scale performance and reliability.
- PySpark, Ray, MLflow, and Airflow compatibility.
- Production Jupyter network security.
- Other operating systems and architectures.

## 12. Final Assessment

**PASS: Tested extended-stack workloads are functionally compatible.**

This assessment applies to the tested package versions
and workloads under CPython 3.15.1 on macOS arm64.

The original baseline readiness percentage remains unchanged.
No new overall readiness percentage is assigned.

## 13. Evidence Provenance

Evidence reviewed from terminal output dated 2026-10-26.

| Time (EDT) | Experiment |
|---|---|
| 12:21:02 | PyYAML source build |
| 12:21:32 | PyYAML extension inspection |
| 12:21:58 | JupyterLab/Dask installation |
| 12:22:33 | Dask Array validation |
| 12:23:09 | Notebook execution |
| 12:24:29 | Dask DataFrame validation |
| 12:25:39 | Initial kernel diagnostic |
| 12:26:13 | Corrected kernel-isolation PASS |

The report does not independently rerun the experiments.

## 14. Recommended Next Steps

1. Review this supplemental report.
2. Reconcile results with the existing readiness methodology.
3. Validate remaining ecosystem packages separately.
4. Run repository tests before any release commit.
5. Commit only reviewed changes.

---

**End of report.**
