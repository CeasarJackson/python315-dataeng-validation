# Python 3.15.0rc2 Validation Runbook

**Project:** Python 3.15 Data Engineering Validation Suite
**Purpose:** Produce a clean, reproducible Python 3.15.0rc2 compatibility baseline while preserving RC1 provenance.

---

## 1. Baseline Rules

The official RC2 baseline must:

- run exactly Python `3.15.0rc2`;
- use ARM64 on this Mac;
- run from a clean Git worktree;
- start with no active `reports/3.15.0rc2/`;
- preserve the validated RC1 report and tag;
- never use `--allow-version-mismatch` or `--allow-dirty`.

Historical quarantine entries such as `3.15.0rc1-MISLABELED-ran-on-b4`
and `3.15.0rc2-PLACEHOLDER-never-run` are evidence only.

## 2. Verify RC1

Verify the RC1 tag and manifest before beginning RC2 work.

Expected RC1 baseline:

- release: `3.15.0rc1`
- runtime: `3.15.0rc1`
- readiness: `77`
- PASS: `11`
- INCOMPAT: `2`
- BLOCKED: `2`
- SKIP: `2`

## 3. Verify RC2 Interpreter

Use the official Python 3.15.0rc2 ARM64 interpreter:

`/Library/Frameworks/Python.framework/Versions/3.15/bin/python3.15`

The interpreter must report exactly `Python 3.15.0rc2`.

## 4. Build the RC2 Environment

Rebuild `.venv` from the verified RC2 interpreter and install:

- `requirements-py315-build.txt`
- `requirements-py315-dataeng-jupyter.txt`
- `requirements-py315-dataeng-extended.txt`

Always run dependency validation against the intended interpreter:

`uv pip check --python .venv/bin/python`

Never use bare `uv pip check` as RC2 evidence while another environment is active.

## 5. Compatibility Classification

Runtime success and upstream declared support are separate signals.

If package metadata excludes Python 3.15, classify the package as `INCOMPAT`
even when import/runtime smoke testing succeeds.

Prefect 3.7.7 currently declares Python `<3.15`.

Wheel availability is also separate from runtime/source-build compatibility.

## 6. Clean Preflight

Before official generation, require:

- exact Python 3.15.0rc2;
- clean Git worktree;
- no active `reports/3.15.0rc2/`;
- expected ARM64 architecture;
- expected interpreter provenance.

Run:

`.venv/bin/python scripts/preflight_release.py --release 3.15.0rc2`

A dirty worktree or existing active RC2 report is a stop condition.

## 7. Validate

Run consolidated validation with:

`PYTHON_BIN=.venv/bin/python bash scripts/validate_all.sh`

Then run:

`.venv/bin/python -m pytest tests -q`

and:

`git diff --check`

Distinguish Python incompatibility from missing wheels, optional dependencies,
Docker/infrastructure gaps, and declared-support metadata.

## 8. Generate RC2 Evidence

Only after the clean preflight passes:

`.venv/bin/python scripts/generate_report.py --release 3.15.0rc2`

The authoritative modern release artifacts are:

- `manifest.json`
- `compatibility_report.md`

Historical PDF assessments must not be silently copied into a new release.

## 9. Verify Identity

The generated manifest must satisfy:

- `release == 3.15.0rc2`
- `python_runtime == 3.15.0rc2`

Any mismatch invalidates the baseline.

## 10. Compare RC1 to RC2

Use `scripts/compare_reports.py` to compare `3.15.0rc1` with `3.15.0rc2`.

Readiness movement is measured, not forced to improve.

A `PASS -> SKIP` caused by unavailable Docker validation is not automatically
a Python compatibility regression.

## 11. Final Gate and Tag

Before committing the RC2 baseline:

- rerun consolidated validation;
- rerun the full repository tests;
- run `git diff --check`;
- review all generated artifacts.

Do not create `python-3.15.0rc2-validation` until the reviewed RC2 baseline has
been committed and merged.

The goal is truthful, reproducible compatibility evidence, not a predetermined
readiness score.
