# Python 3.15 Data Engineering Validation Lab v2.1.0

## Summary

v2.1.0 adds the Python 3.15.1 validation cycle: a reconciled, evidence-based
readiness result of **94% (PROVISIONAL)**, a Python 3.15.1 Docker image for the
PySpark and Arrow checks, and a standards pass over the scripts and shell
runners.

Version numbering: tags are out of date order (`v2.0.0`, 2026-06-19, precedes
`v1.10.0`, 2026-10-11). v2.1.0 is the next suite version after both.

## Highlights

### Python 3.15.1 readiness

- Official result from `reports/3.15.1/evidence.json`: 15 PASS, 2 BLOCKED
  (MLflow, Ray; both upstream), 0 FAIL, 0 SKIP, scoring 94% PROVISIONAL.
- The first 3.15.1 run (17%) is kept unchanged as `manifest.baseline.json`;
  the reconciliation and comparison are documented in `reports/3.15.1/`.
- Evidence ingestion is reproducible (`scripts/ingest_evidence.py`).

### PySpark and Arrow on Python 3.15.1

- New Docker image `docker/pyarrow_lab_py315` (python:3.15.1-slim, OpenJDK 21):
  PySpark 4.2.0, PyArrow 26.0.0, pandas 3.1.0. The earlier `py314` image never
  tested 3.15.1.
- The report generator records the container's Python and image in the
  manifest and fails with a reason if the Python is wrong for the image.
- Opt-in integration tests (`RUN_DOCKER_INTEGRATION=1`) cover nullable columns,
  a pandas UDF, and nested struct, array, map, timestamp and decimal types.
- Known warning: PySpark reports that it does not support pandas >= 3.0; it
  did not affect any tested workload.

### Standards pass

- Ctrl-C now exits 130 across `scripts/` and `tools/` (previously a traceback,
  and exit 1 for `tools/sync_readiness.py`).
- `scripts/fix_repository_headers.py` rewritten: shared logger, `--check`,
  `--dry-run`, backups before writing, read-back verification, shebang-safe.
- The five `*_tests/run_*_validation.sh` runners rewritten (strict mode, `IFS`,
  `DRY_RUN=1`, `PYTHON=` override, colored console plus plain-text log).
  This fixes a bug where the polars and sqlalchemy runners could print
  "VALIDATION PASSED" after a failed step.
- `scripts/release.sh` and `scripts/validate_all.sh`: `IFS`, color only on a
  terminal, plain-text log file, documented exit codes; the dry run no longer
  claims an archive was built.
- New tests: shell standards (static and behavioral), interrupt handling,
  and `fix_repository_headers`.

## Validation

- Full suite on Python 3.15.1: 299 passed, 1 skipped (the opt-in Docker
  integration test), with `-X warn_default_encoding -W error`.
- Black and Ruff clean over `scripts`, `tests` and `tools`.
- `scripts/release.sh v2.1.0 --dry-run` completes with exit 0 and creates no
  artifacts.

## Known limitations

- The 94% is PROVISIONAL. MLflow and Ray remain BLOCKED upstream.
- Prefect's declared Python support (PRE-001) is tracked in
  `docs/KNOWN_ISSUES.md`.
- Four modules still have no `main()` (exempted and listed in
  `tests/test_script_interrupt_handling.py`); several legacy scripts still use
  `print` rather than the shared logger.

## Release Artifacts

- `releases/python315-dataeng-validation-v2.1.0.zip`
- `releases/python315-dataeng-validation-v2.1.0.zip.sha256`

## Tag

- `v2.1.0`
