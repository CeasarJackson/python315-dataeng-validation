# Python 3.15 Data Engineering Validation Lab v2.2.0

## Summary

v2.2.0 adds the Python 3.15.2 validation cycle: a reconciled, evidence-based
readiness result of **94% (PROVISIONAL)** against a recorded 88% baseline, a
reproducible PDF assessment, stricter handling of container evidence, and a
release builder that can no longer stamp a build with the wrong interpreter.

Version numbering: v2.2.0 is the next suite version after v2.1.0, which
covered Python 3.15.1.

## Highlights

### Python 3.15.2 readiness

- Result from `reports/3.15.2/evidence.json`: 15 PASS, 2 BLOCKED (MLflow, Ray),
  0 FAIL, 0 SKIP, scoring 94% PROVISIONAL.
- The first 3.15.2 run (88%) is kept unchanged as `manifest.baseline.json`;
  the reconciliation and the baseline-to-reconciled comparison are documented
  in `reports/3.15.2/`.
- Prefect 3.9.0 passes on Python 3.15.2. Pinned in
  `requirements-py315-dataeng-extended.txt` together with Dask 2026.7.1;
  Ray, MLflow and Airflow are deliberately not pinned, and the file now says
  why. PRE-001 in `docs/KNOWN_ISSUES.md` is updated and stays OPEN.
- New lock files: `requirements-py315-core-3.15.2.lock.txt` and
  `requirements-py315-extended-3.15.2.lock.txt`.
- `tools/sync_readiness.py` and `scripts/generate_report.py` were checked to
  use the same readiness formula (SKIP excluded, BLOCKED 0.5, INCOMPAT 0.25,
  capped at 100).

### Assessment PDF and Docker evidence

- `scripts/build_assessment_pdf.py` renders
  `reports/3.15.2/PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf` purely from
  `manifest.json`. Output is byte-identical for identical input, it runs the
  readiness consistency check first, and it refuses to overwrite without
  `--force`.
- A Docker-sourced result counts as release evidence only when the recorded
  evidence states `worker interpreter reporting Python <runtime>`. An image tag
  alone, a different version, or a longer version such as 3.15.20 is rejected.
  The check is a single function with parametrized regression tests.
- The PDF's sensitivity line is worded as an analysis ("hypothetically
  excluding all Docker-sourced results"), not as a second headline.

### Release builder hardening (`scripts/release.sh`)

- Real builds require `--python-release X.Y.Z` and refuse an interpreter that
  reports a different release. This closes a trap where a stale `.venv`
  (Python 3.15.0) was the silent fallback interpreter.
- The Python release is read from the interpreter, and the canonical
  `reports/<release>/manifest.json` must exist and name that release before
  readiness is synchronized.
- Existing archive or checksum files, including dangling symlinks, are
  rejected before tests or readiness synchronization run. The script no longer
  deletes a previous same-version archive.
- Regression tests in `tests/test_shell_standards.py` cover a missing flag,
  malformed values and an interpreter mismatch.

### Tests

- Readiness consistency and report completeness checks now cover the 3.15.1 and
  3.15.2 manifests and Markdown reports.
- New `tests/test_build_assessment_pdf.py` (PDF generator and evidence rule).

## Validation

- Full suite on Python 3.15.2: 331 passed, 1 skipped (the opt-in Docker
  integration test, `RUN_DOCKER_INTEGRATION=1`).
- `uv pip check` on the validation environment: all installed packages
  compatible.
- `scripts/release.sh v2.2.0 --python-release 3.15.2 --dry-run` completes with
  exit 0 and creates no artifacts.

## Known limitations

- The 94% is PROVISIONAL (local mode, single machine). MLflow and Ray remain
  BLOCKED; see `reports/3.15.2/evidence.json`.
- The generated PDF headline does not yet carry a PROVISIONAL qualifier.
- Generated reports still print "Suite version 1.2.0", a value hardcoded in
  `scripts/generate_report.py`; it does not track the suite release.
- Open items in `reports/3.15.2/RELEASE_CHECKLIST.md` at release time include
  the explicit-encoding audit, the removed-names scan, rebuilding `.venv` on
  3.15.2, and the Tachyon, GC/JIT and free-threaded notes.
- Four modules still have no `main()`, and several legacy scripts still use
  `print` rather than the shared logger.

## Release Artifacts

- `releases/python315-dataeng-validation-v2.2.0.zip`
- `releases/python315-dataeng-validation-v2.2.0.zip.sha256`

## Tag

- `v2.2.0`
