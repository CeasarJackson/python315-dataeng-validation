# Python 3.15.2 Core Stack Checkpoint

**Author:** Dr. Ceasar Jackson Jr.
**Date:** 2026-10-27
**Platform:** macOS arm64
**Python:** 3.15.2 (Homebrew `python@3.15`)
**Environment:** `.venv3152`
**Status:** CORE CHECKPOINT PASSED - no readiness score assigned

## 1. Why this exists

On 2026-10-27 the Homebrew maintenance run upgraded `python@3.15` from 3.15.1
to 3.15.2 and removed 3.15.1. `.venv3151` links to the Homebrew interpreter, so
it silently began running 3.15.2 while keeping its name. The 3.15.1 release
(v2.1.0, 94% PROVISIONAL) was validated on 2026-10-26, before the upgrade, and
is unaffected. This note records what was verified on 3.15.2 afterwards.

## 2. What was done

1. Captured the 30-package inventory from the existing environment
   (`logs/python3152_source_packages_20261027_111253.txt`, sha256
   `78c033495906a717fdae32048bee61ec8b564f8ee413d4951260d755ff5928dd`).
2. Built a fresh venv: `uv venv .venv3152` on Python 3.15.2.
3. Installed the same 30 pinned packages (`Installed 30 packages`).
4. Compared inventories: identical.

## 3. Results

| Check | Result |
|---|---|
| `uv pip check` (both environments) | All installed packages are compatible |
| `pytest -q` | 299 passed, 1 skipped |
| `pytest -q -X warn_default_encoding -W error` | 299 passed, 1 skipped |
| `scripts/validate_all.sh` | sqlite, sqlalchemy, duckdb, polars suites PASS; airflow suite SKIP (not installed) |
| Imports | duckdb 2.0.0, numpy 2.5.4, pandas 3.1.0, polars 1.41.2, pyarrow 26.0.0, pydantic 2.14.1, SQLAlchemy 2.0.50 |

The one skipped test is the opt-in Docker integration test
(`RUN_DOCKER_INTEGRATION=1`).

## 4. What this does not show

- The inventory match is expected: the snapshot came from the old venv. It
  shows reproducibility, not a 3.15.1 versus 3.15.2 comparison.
- Only the core stack was exercised. Prefect, dask, Ray, MLflow, Airflow and
  PySpark (Docker) have not been run on 3.15.2.
- `docker/pyarrow_lab_py315` is still pinned to `python:3.15.1-slim`, so the
  PySpark evidence remains a 3.15.1 result.
- No readiness percentage is claimed for 3.15.2. That requires the full
  evidence ladder and `generate_report.py --release 3.15.2`.

## 5. Reproducing

`requirements-py315-core-3.15.2.lock.txt` holds the exact package set. See its
header for commands. The older `requirements-py315-*` files do not reproduce
this environment (they pin pandas 3.0.3, numpy 2.4.6 and duckdb 1.5.3 and omit
pyarrow).

## 6. Next steps

1. Update the Docker image to `python:3.15.2-slim` and re-run the PySpark and
   Arrow checks.
2. Install the extended stack and run the evidence ladder for 3.15.2.
3. Do not reuse `.venv3151` for new evidence; its name no longer matches its
   interpreter.
