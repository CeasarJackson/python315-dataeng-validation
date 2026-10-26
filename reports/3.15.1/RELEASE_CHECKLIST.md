# Release Checklist: Python 3.15.1

**Scaffolded:** 2026-10-26
**Previous cycle:** 3.15.0

## 1. Produce real data (do these first, in order)

- [ ] `uv python install 3.15.1` and rebuild `.venv` on the final interpreter
- [ ] `python scripts/validate_py315.py`
- [ ] `python scripts/validate_core.py`
- [ ] `python scripts/validate_stack.py`
- [ ] `python scripts/validate_extended.py`
- [ ] `python scripts/generate_report.py --release 3.15.1`
- [ ] `python tools/sync_readiness.py`
- [ ] `python scripts/compare_reports.py 3.15.0 3.15.1`
- [ ] Copy `PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf` into this directory

## 2. Interpreter changes that touch this suite

### UTF-8 is now the default encoding (PEP 686)
- [ ] Add `encoding="utf-8"` to every `read_text()` / `write_text()` / `open()`
      call. Known gaps: `scripts/generate_report.py` (`write_text`),
      `scripts/compare_reports.py` (`read_text`), `scripts/fix_repository_headers.py`
- [ ] Run once with `-X warn_default_encoding` to list any remaining calls

### Lazy imports (PEP 810)
- [ ] Confirm probes still fail eagerly. A `lazy import` defers `ImportError`
      to first use, so `probe_package()` and the `find_spec` guards must not
      be run under `PYTHON_LAZY_IMPORTS=all`
- [ ] Add one test that runs the probes with `-X lazy_imports=all` and asserts
      the result matches normal mode (or documents the difference)

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
- [ ] `importlib.metadata.metadata()` now raises `MetadataNotFound` for a
      metadata directory with no metadata file; `get_version()` in
      `generate_report.py` only catches `PackageNotFoundError`
- [ ] `.pth` `import` lines are silently deprecated in favour of `.start`
      files (PEP 829); note any package in the venv relying on them
- [ ] Frame pointers are on by default (PEP 831); expect small build/perf
      differences versus rc builds if they were compiled differently

### Packaging / ABI
- [ ] Re-check PyPI for `cp315` wheels of the BLOCKED packages (pyarrow, ray)
- [ ] Free-threaded wheels are separate (`cp315t`); `abi3t` is not yet
      supported by common build backends per the changelog
- [ ] Re-run the Docker PySpark probe; the image tag is still `py314`

## 3. VERIFY before publishing

- [ ] Prefect INCOMPAT reason (`typing.no_type_check_decorator` removed):
      the changelog's **Removed > typing** section was not reachable when
      this checklist was written. Confirm against
      docs.python.org/3.15/whatsnew/3.15.html#removed and the changelog
- [ ] Any other Removed entries (ast, collections.abc, ctypes, datetime, glob,
      importlib, importlib.resources, pathlib, platform, sysconfig, threading,
      types, wave, zipimport) against packages in the tested stack
- [ ] JIT speedup claims: measure with `benchmark_pandas_polars.py`; do not
      quote a figure from a course or blog

## 4. Repository housekeeping

### Tests
- [ ] `tests/test_release_progression.py` and
      `tests/test_release_history_integrity.py` auto-discover release
      directories from disk. No edit needed; just confirm `3.15.1` is picked up
- [ ] `tests/test_report_completeness.py`: add this directory to
      `EXTENDED_REPORTS` (still hardcoded)
- [ ] `tests/test_readiness_consistency.py`: `REPORT_DIR` is still hardcoded
      to `3.15.0b2`; point it at `3.15.1`
- [ ] `python -m pytest -q`

### Generation order and guards
- [ ] `generate_report.py` refuses to label a report with a release the
      running interpreter is not. Rebuild `.venv` first, then reinstall
      dependencies (`colorlog` included) before generating
- [ ] Run `tools/sync_readiness.py` after report generation so the manifest
      and Markdown readiness markers are synchronized
- [ ] Confirm `generate_report.py` and `tools/sync_readiness.py` still use the
      same readiness formula: SKIP excluded from the denominator, BLOCKED
      weighted 0.50, INCOMPAT weighted 0.25, and readiness capped at 100%

### Cleanup
- [ ] `reports/3.15.0ga/` holds only `.gitkeep`; use canonical
      `reports/3.15.1` and remove the empty directory
- [ ] `bash scripts/release.sh <suite-version>` (the suite version, not the
      Python version)
