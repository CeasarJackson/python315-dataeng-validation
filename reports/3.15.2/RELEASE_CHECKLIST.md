# Release Checklist: Python 3.15.2

**Scaffolded:** 2026-10-27
**Previous cycle:** 3.15.1

## 1. Produce real data (do these first, in order)

- [ ] `uv python install 3.15.2` and rebuild `.venv` on the final interpreter
- [ ] `python scripts/validate_py315.py`
- [ ] `python scripts/validate_core.py`
- [ ] `python scripts/validate_stack.py`
- [ ] `python scripts/validate_extended.py`
- [x] `python scripts/generate_report.py --release 3.15.2 --docker-image pyarrow-dataeng:py3152`
      (core-env baseline; extended packages reconciled through evidence.json)
- [x] `python tools/sync_readiness.py --release 3.15.2` (run on the promoted reconciled manifest)
- [x] `python scripts/compare_reports.py 3.15.1 3.15.2` (2026-10-27: 15 PASS / 0 FAIL / 0 INCOMPAT
      on both; 17 packages unchanged in status. Version bumps are not part of the delta)
- [x] `PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf` generated from manifest.json with
      scripts/build_assessment_pdf.py (commit fb1761a; sha256 9ff01e37...0e7b; deterministic)

## 2. Interpreter changes that touch this suite

### UTF-8 is now the default encoding (PEP 686)
- [ ] Add `encoding="utf-8"` to every `read_text()` / `write_text()` / `open()`
      call. Known gaps: `scripts/generate_report.py` (`write_text`),
      `scripts/compare_reports.py` (`read_text`), `scripts/fix_repository_headers.py`
- [ ] Run once with `-X warn_default_encoding` to list any remaining calls

### Lazy imports (PEP 810)
- [x] Confirm probes still fail eagerly under forced lazy imports.
      VERIFIED 2026-10-27: tests/test_lazy_imports_probes.py passed.
- [x] Test probes with `-X lazy_imports=all` against normal mode.
      VERIFIED 2026-10-27: both lazy-import regression tests passed.

### frozendict is not a dict subclass (PEP 814)
- [ ] Grep for `isinstance(x, dict)`; use `collections.abc.Mapping` where a
      frozen mapping could legitimately arrive
- [ ] Decide whether manifest `results` should load with
      `object_pairs_hook=frozendict` (json now accepts it)

### Profiling package (PEP 799)
- [ ] Add a Tachyon (`profiling.sampling`) run to the benchmark scripts
- [ ] `profile` module is deprecated, removal in 3.17; confirm the suite does
      not import it

### Other verified items
- [ ] `argparse` `suggest_on_error` now defaults to True; re-check `--help`
      snapshots if any test compares CLI output
- [ ] Color is now on by default in more stdlib CLIs; set `NO_COLOR=1` in CI
      log capture to keep logs free of escape codes
- [ ] GC: 3.15 uses the generational GC (the incremental GC was reverted);
      re-baseline any memory numbers taken on 3.14.0-3.14.4
- [x] Verify Python 3.15 missing-metadata exception handling.
      VERIFIED 2026-10-27: tests/test_get_version_metadata.py passed;
      generate_report.py and validate_dataeng_stack.py handle FileNotFoundError.
- [ ] `.pth` `import` lines are silently deprecated in favour of `.start`
      files (PEP 829); note any package in the venv relying on them
- [ ] Frame pointers are on by default (PEP 831); expect small build/perf
      differences versus rc builds if they were compiled differently

### Packaging / ABI
- [x] Re-check PyPI for `cp315` wheels of the BLOCKED packages (pyarrow, ray)
      DONE 2026-10-27: pyarrow 26.0.0 has a cp315 wheel (no longer blocked); ray 2.59.0 still
      publishes cp310-cp314 only; mlflow is blocked by its own pyarrow<26 cap
- [ ] Free-threaded wheels are separate (`cp315t`); `abi3t` is not yet
      supported by common build backends per the changelog
- [x] Re-run the Docker PySpark probe with an image that runs the release's own
      Python (docker/pyarrow_lab_py315 for 3.15.x); py314 tests Python 3.14
      DONE 2026-10-27: pyarrow-dataeng:py3152 (python:3.15.2-slim); baseline probe and
      integration test passed

## 3. VERIFY before publishing

- [x] Prefect and `typing.no_type_check_decorator`: SUPERSEDED 2026-10-27. Prefect 3.9.0
      has a clean `uv pip check` and runs flows on 3.15.2 (PASS recorded). Prefect 3.7.x
      stays unusable on a current resolve (starlette/FastAPI conflict, not the
      interpreter). See READINESS_RECONCILIATION_2026-10-27.md and docs/KNOWN_ISSUES.md
- [ ] Scan the stack for every name on the official Removed list
      (docs.python.org/3.15/whatsnew/3.15.html#removed): ast, collections.abc,
      ctypes, datetime, glob, http.server, importlib, importlib.resources,
      pathlib, platform, sre_*, sysconfig, threading, types, typing, wave,
      zipimport
- [ ] JIT speedup claims: measure with `benchmark_pandas_polars.py`; do not
      quote a figure from a course or blog

## 4. Repository housekeeping

### Tests
- [ ] `tests/test_release_progression.py` and
      `tests/test_release_history_integrity.py` auto-discover release
      directories from disk. No edit needed; just confirm `3.15.2` is picked up
- [x] `tests/test_report_completeness.py`: add this directory to
      `EXTENDED_REPORTS` (still hardcoded)
- [x] `tests/test_readiness_consistency.py`: `REPORT_DIR` is still hardcoded
      to `3.15.0b2`; point it at `3.15.2`
      DONE 2026-10-27 (commit 8e617b2): it was already on 3.15.1, which keeps the JSON/PDF
      checks; new parametrized checks cover 3.15.1 and 3.15.2 manifests and readiness docs.
      The JSON/PDF checks for 3.15.2 wait for those artifacts
- [x] `python -m pytest -q`: 316 passed, 1 skipped after commit 8e617b2.
      UPDATED 2026-10-27: full suite 325 passed, 1 skipped; targeted
      compatibility suite 59 passed. Docker integration requires
      RUN_DOCKER_INTEGRATION=1.

### Generation order and guards
- [ ] `generate_report.py` refuses to label a report with a release the
      running interpreter is not. Rebuild `.venv` first, then reinstall
      dependencies (`colorlog` included) before generating
- [x] Run `tools/sync_readiness.py` after report generation so the manifest
      and Markdown readiness markers are synchronized
      DONE 2026-10-27 13:21 on the promoted manifest (backup of pre-sync files kept
      locally); manifest and all three Markdown reports state 94%
- [x] Confirm `generate_report.py` and `tools/sync_readiness.py` use the
      same readiness formula: SKIP excluded from the denominator, BLOCKED
      weighted 0.50, INCOMPAT weighted 0.25, and readiness capped at 100%.
      VERIFIED 2026-10-27: implementations inspected; readiness regression
      suite 101 passed; baseline 88% and promoted provisional readiness 94%.

### Cleanup
- [ ] `reports/3.15.0ga/` holds only `.gitkeep`; use canonical
      `reports/3.15.2` and remove the empty directory
- [ ] `bash scripts/release.sh <suite-version>` (the suite version, not the
      Python version)
