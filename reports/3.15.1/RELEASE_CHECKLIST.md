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
- [x] Add `encoding="utf-8"` to every `read_text()` / `write_text()` / `open()`
      call. Done 2026-10-26: an AST scan of `scripts/`, `tools/` and `tests/`
      found 39 text-mode sites without it in 9 files (scripts: benchmark_pandas_polars,
      check_cp315_wheels, fix_repository_headers, compare_reports; tools:
      build_reports_system, fix_repo_docs, update_docs; tests:
      generate_report_provenance, preflight_release); all now pass it, and a
      re-scan finds 0. Behavior is unchanged on 3.15 (UTF-8 is the default); it
      matters for older interpreters and Windows
- [x] Run once with `-X warn_default_encoding` to list any remaining calls.
      Done 2026-10-26 on 3.15.1: `-X warn_default_encoding -m pytest -q -W error`
      passed (215 passed, 1 skipped), so no EncodingWarning is raised by any
      code the suite exercises. Re-run with colorlog 6.12.0 installed: 216 passed

### Lazy imports (PEP 810)
- [x] Confirm probes still fail eagerly. A `lazy import` defers `ImportError`
      to first use, so `probe_package()` and the `find_spec` guards must not
      be run under `PYTHON_LAZY_IMPORTS=all`
      Done 2026-10-26 on 3.15.1: probes run under `-X lazy_imports=all` give
      the same results as `normal`; a missing package still reports FAIL
- [x] Add one test that runs the probes with `-X lazy_imports=all` and asserts
      the result matches normal mode (or documents the difference)
      Done 2026-10-26: `tests/test_lazy_imports_probes.py` (2 passed on 3.15.1;
      229 passed in the full suite with `-X warn_default_encoding -W error`).
      Note: valid values are `all` or `normal` (there is no `none`)

### frozendict is not a dict subclass (PEP 814)
- [x] Grep for `isinstance(x, dict)` (audited 2026-10-26: 5 sites, all on
      `json.loads` output, always a plain dict; no change needed); use `collections.abc.Mapping` where a
      frozen mapping could legitimately arrive
- [ ] Decide whether manifest `results` should load with
      `object_pairs_hook=frozendict` (json now accepts it)

### Profiling package (PEP 799)
- [x] Add a Tachyon (`profiling.sampling`) run to the benchmark scripts
      Done 2026-10-26: Tachyon is CLI-only (no Python API), so
      `scripts/profile_with_tachyon.py` wraps `python -m profiling.sampling run`
      and leaves the benchmarks unchanged. Output goes to `outputs/profiles/`
      (gitignored). Unit-tested without the profiler (`tests/test_profile_with_tachyon.py`).
      NOT YET RUN on 3.15.1: macOS may need root or the debugger entitlement
- [x] `profile` module is deprecated, removal in 3.17; confirmed 2026-10-26
      that no script, tool or test imports it

### Other verified items
- [x] `argparse` `suggest_on_error` now defaults to True; confirmed 2026-10-26
      that no test compares `--help` output
- [x] Color is now on by default in more stdlib CLIs; set `NO_COLOR=1` in CI
      log capture to keep logs free of escape codes. Done 2026-10-26:
      `scripts/logger.py` honors `NO_COLOR` and emits no escapes when stdout is
      not a terminal; the file log is always plain text
      (`tests/test_logger_sinks.py`, verified on 3.15.1 with colorlog 6.12.0)
- [ ] GC: 3.15 uses the generational GC (the incremental GC was reverted);
      re-baseline any memory numbers taken on 3.14.0-3.14.4
- [x] `importlib.metadata.metadata()` now raises `MetadataNotFound` for a
      metadata directory with no metadata file. Confirmed on 3.15.1 (2026-10-26):
      `MetadataNotFound` subclasses `FileNotFoundError`, NOT `PackageNotFoundError`,
      so `get_version()` would have crashed on a broken install. Fixed in
      `generate_report.py` (reports "metadata missing") and
      `validate_dataeng_stack.py`; tests in `tests/test_get_version_metadata.py`
- [x] `.pth` `import` lines are silently deprecated in favour of `.start`
      files (PEP 829); checked 2026-10-26: `.venv3151` contains no `.pth` files
- [ ] Frame pointers are on by default (PEP 831); expect small build/perf
      differences versus rc builds if they were compiled differently

### Packaging / ABI
- [ ] Re-check PyPI for `cp315` wheels of the BLOCKED packages (pyarrow, ray)
- [ ] Free-threaded wheels are separate (`cp315t`); `abi3t` is not yet
      supported by common build backends per the changelog
- [ ] Re-run the Docker PySpark probe; the image tag is still `py314`

## 3. VERIFY before publishing

- [x] Prefect INCOMPAT reason (`typing.no_type_check_decorator` removed):
      CONFIRMED REMOVED in 3.15 (What's New > Removed > typing). Mechanism, per
      docs/KNOWN_ISSUES.md: prefect 3.7.x reached it through a transitive
      import (beartype 0.22.9; 0.23.0 no longer fails), and 3.7.7 declares
      `<3.15`. Current prefect 3.9.0 has a clean `uv pip check` and runs flows
      on 3.15.1 (evidence level Functional). Remaining EventsWorker log errors
      reproduce on 3.14.10, so they are not 3.15-specific. See
      READINESS_RECONCILIATION_2026-10-26_v2.md
- [x] Other Removed entries (ast, collections.abc, ctypes, datetime, glob,
      http.server, importlib, importlib.resources, pathlib, platform, sre_*,
      sysconfig, threading, types, typing, wave, zipimport) checked 2026-10-26
      against the official Removed list: a name scan of `scripts/`, `tools/`,
      `tests/` and `.venv3151` site-packages (5,636 files) found no use of any
      removed API. All hits were text only (a WebIDL type name, comments,
      docstrings, the string checks for the Prefect case above), plus six's own
      `load_module`, which also defines `exec_module`. Not statically
      checkable: ast node construction rules. Scope: the baseline venv only;
      the isolated Prefect, MLflow, Airflow and PySpark environments were
      validated by running workloads instead
      NOTE: `tools/build_reports_system.py` and `tools/fix_repo_docs.py` still
      carry the Prefect 3.7.x text; they generate the 3.15.0b1-era documents and
      are period-accurate, so they were left unchanged. The release scaffold
      template (`scripts/scaffold_release.py`) was updated
- [x] JIT speedup claims: none made. Checked 2026-10-26: no JIT or speedup
      figure appears in the 3.15.1 reports or the README. Measure with
      `benchmark_pandas_polars.py` before adding one

## 4. Repository housekeeping

### Tests
- [x] `tests/test_release_progression.py` and
      `tests/test_release_history_integrity.py` auto-discover release
      directories from disk. Confirmed 2026-10-26: `3.15.1` is picked up
- [x] `tests/test_report_completeness.py`: `3.15.1` added to
      `EXTENDED_REPORTS` (still a hardcoded list; add future releases by hand)
- [x] `tests/test_readiness_consistency.py`: `REPORT_DIR` now points at
      `3.15.1` (done 2026-10-26, commit 0059a64). `readiness_matrix.json` was
      derived from `manifest.json` and the PDF built with
      `build_assessment_pdf.py --release 3.15.1 --previous 3.15.0`
- [x] `python -m pytest -q` (177 passed on Python 3.15.1, commit a1a2fea, 2026-10-26)

### Generation order and guards
- [x] `generate_report.py` refuses to label a report with a release the
      running interpreter is not. Guard tested 2026-10-26
      (`tests/test_release_runtime_guard.py`: mismatch exits 1 before any probe
      or write; override warns the report is not a validation; confirmed the
      tests fail if the guard is disabled). For every future cycle:
      rebuild `.venv` first, then reinstall dependencies (`colorlog`
      included) before generating
- [ ] Run `tools/sync_readiness.py` after report generation so the manifest
      and Markdown readiness markers are synchronized
- [x] `generate_report.py` and `tools/sync_readiness.py` use the same readiness
      formula (SKIP excluded from the denominator, BLOCKED 0.50, INCOMPAT 0.25,
      capped at 100%). Verified 2026-10-26 by running both real implementations
      over 1,023 status combinations: 0 mismatches

### Cleanup
- [x] `reports/3.15.0ga/`: directory no longer exists (checked 2026-10-26);
      canonical directory is `reports/3.15.1`
- [ ] `bash scripts/release.sh <suite-version>` (the suite version, not the
      Python version)
