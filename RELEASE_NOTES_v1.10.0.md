# Python 3.15 Data Engineering Validation Lab v1.10.0

## Summary

v1.10.0 adds the Python 3.15.0 (GA) validation baseline: **92% readiness**
(82% at rc2), measured on Python 3.15.0 final, macOS 27.0.1 ARM64, tested
2026-10-10. Readiness is 91% if the Docker-sourced PySpark result is not
counted (see Limitations).

## Results (17 packages, compared with 3.15.0rc2)

| Status | rc2 | GA |
|--------|-----|----|
| PASS | 10 | 13 |
| INCOMPAT | 2 | 1 |
| BLOCKED | 2 | 1 |
| SKIP | 3 | 2 |
| FAIL | 0 | 0 |

- **pyarrow** BLOCKED to PASS (26.0.0; cp315 wheel now published).
- **dask.dataframe** INCOMPAT to PASS (it only depended on pyarrow).
- **pyspark** SKIP to PASS. This is a coverage change: it ran in the `py314`
  Docker image and is not Python 3.15 evidence.
- **Prefect** remains INCOMPAT (declares Python `<3.15`; a flow smoke run
  succeeded this time).
- **Ray** remains BLOCKED (newest release ships wheels only through cp314).
- **MLflow** and **Apache Airflow** remain SKIP (not installed).

## Highlights

- Added `reports/3.15.0/`: manifest, compatibility report, readiness matrix
  (Markdown and JSON), executive summary, full assessment and assessment PDF.
- Added `scripts/build_assessment_pdf.py`, which renders the assessment PDF
  from the manifest and refuses to render an inconsistent manifest (release
  mismatch, counter mismatch, readiness not matching the formula). Output is
  deterministic.
- Fixed stale `3.15.0ga` references; the canonical directory is `reports/3.15.0`.
- Pointed `test_readiness_consistency.py` and `test_report_completeness.py`
  at the 3.15.0 report.
- Recorded GA evidence in `docs/KNOWN_ISSUES.md` (ARW-001 resolved; RAY-001 and
  PRE-001 re-verified).
- Reconciled readiness values in six earlier manifests that no longer matched
  the project formula: 3.15.0b2 84 to 90, 3.15.0b4 77 to 83, 3.15.0rc1 77 to 83,
  3.15 85 to 90, v1.9.2 85 to 90, v1.9.3 85 to 89. The documentation already
  cited the recomputed values.

## Limitations

- `environment_consistent` is false (Prefect's declared Python range).
- `pyarrow_tests/` is an empty placeholder; the pyarrow PASS rests on the
  report probe plus a one-off functional smoke check that is not stored in
  the repository.
- Delta Lake and fastparquet were not re-tested.
- The PySpark result comes from a Python 3.14 container image.

## Validation

- 105 repository tests passing on Python 3.15.0.
- Preflight passed on a clean worktree with no pre-existing 3.15.0 report.

## Release Artifacts

- `releases/python315-dataeng-validation-v1.10.0.zip`
- `releases/python315-dataeng-validation-v1.10.0.zip.sha256`

## Tag

- `v1.10.0`
