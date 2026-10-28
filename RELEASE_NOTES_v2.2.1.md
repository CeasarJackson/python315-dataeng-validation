# Python 3.15 Data Engineering Validation Lab — v2.2.1

**Release date:** 2026-10-28
**Suite version:** v2.2.1
**Python runtime:** 3.15.2
**Readiness:** 94% PROVISIONAL

## Overview

This maintenance release improves explicit UTF-8 handling in subprocess
text-mode calls, test formatting, and compatibility audit documentation.

Production readiness remains **94% PROVISIONAL**; full production
readiness has not been established.

## Changes Since v2.2.0

### Explicit UTF-8 Encoding

Added explicit `encoding="utf-8"` to subprocess text-mode calls.

Validation subsequently passed with strict encoding warnings enabled.

Commit: `09276aa`

### Test Formatting

Applied Black formatting to the PDF assessment generator tests.

Commit: `9256ee5`

### Validation Documentation

Updated the Python 3.15.2 release checklist to record:

- UTF-8 encoding audit results.
- Strict encoding-warning test results.
- Removed-name compatibility scanning.
- Remaining validation limitations.

The AST audit examined 104 text-mode call sites with zero missing
explicit encodings. The removed-name scan examined 213 tracked text
files without finding first-party use of the scanned removed names.
Dynamic calls and installed third-party code were not fully audited.

Commit: `b7d9590`

## Validation Results

- Python interpreter: 3.15.2.
- Pytest: 331 passed, 1 skipped.
- Strict encoding-warning pytest run: 331 passed, 1 skipped.
- Dependency integrity: 30 installed packages compatible.
- Production readiness: 94% PROVISIONAL.
- Package assessment: 15 PASS, 2 BLOCKED, 0 FAIL, 0 INCOMPAT, 0 SKIP.
- Readiness manifest synchronization: byte-identical.
- Git working tree: clean at documentation preflight.

The skipped test requires an explicitly enabled Docker integration run.

## Known Limitations

- MLflow remains blocked by its PyArrow dependency constraint.
- Ray remains blocked pending compatible Python 3.15 wheels.
- Readiness is not 100%; this release must not be represented as fully
  production-ready.
- Encoding-warning test coverage does not establish that every CLI-only
  execution path has been exercised.

- The canonical manifest retains `suite_version: 1.2.0`; this
  maintenance release does not change that metadata.

## Packaging

The release archive is built from **committed Git HEAD** using
`scripts/release.sh v2.2.1 --python-release 3.15.2` with `PYTHON_BIN`
pointing to the Python 3.15.2 interpreter.

Release notes and process documentation must be committed before
building the archive. Verify the ZIP and SHA-256 checksum before
committing release artifacts, tagging, or publishing.

## Release Integrity

The existing v2.2.0 release and its published artifacts are preserved.
