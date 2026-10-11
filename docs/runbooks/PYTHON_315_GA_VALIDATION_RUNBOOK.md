# Python 3.15.0 (GA) Validation Runbook

**Project:** Python 3.15 Data Engineering Validation Suite
**Purpose:** Produce a clean, reproducible Python 3.15.0 final compatibility
baseline, measured against the validated RC2 baseline.
**Status:** READY, NOT RUN. As of 2026-10-03 the CPython FTP directory
(`https://www.python.org/ftp/python/3.15.0/`) lists only up to `3.15.0rc2`;
no final `Python-3.15.0` tarball exists yet. Do not start until it does.

---

## 0. Go / No-Go

Proceed only when all are true:

- `Python-3.15.0.tgz` (final, not `rc*`) exists on python.org.
- The macOS ARM64 installer for 3.15.0 is installed.
- The Git worktree is clean and `main` is up to date.

If any is false, stop. Do not fabricate or pre-fill GA numbers; the repo has
already quarantined one placeholder report (`3.15.0rc2-PLACEHOLDER-never-run`).

## 1. Baseline Rules (same as RC2)

The GA baseline must:

- run exactly Python `3.15.0` (not `3.15.0rc2`);
- use ARM64 on the Mac, from a clean worktree;
- start with no active `reports/3.15.0/`;
- never use `--allow-version-mismatch` or `--allow-dirty`.

Report directory name: **`3.15.0`** (canonical `reports/{release}`). The empty
`reports/3.15.0ga/` placeholder is retired; note that `tools/update_docs.py`
still mentions `3.15.0ga` and will need updating before it is run again.

## 2. Verify the RC2 comparison baseline

Read `reports/3.15.0rc2/manifest.json`. Expected:

- release / runtime: `3.15.0rc2`
- readiness (via `tools/sync_readiness.py`): `82`
- PASS 10, FAIL 0, INCOMPAT 2, BLOCKED 2, SKIP 3 (17 packages)
- `environment_consistent: false` (Prefect declares Python `<3.15`)

GA is compared against this, not against the suspect b2 baseline
(see `docs/KNOWN_ISSUES.md`).

## 3. Verify the interpreter

`/Library/Frameworks/Python.framework/Versions/3.15/bin/python3.15 --version`
must print exactly `Python 3.15.0`.

## 4. Build the environment

Rebuild `.venv` from that interpreter and install:

- `requirements-py315-build.txt`
- `requirements-py315-dataeng-jupyter.txt`
- `requirements-py315-dataeng-extended.txt`

Validate with `uv pip check --python .venv/bin/python` (never bare `uv pip check`).

Re-check items that were blockers at RC2, because GA wheels may now exist:

- PyArrow cp315 wheels (and the cascade: dask.dataframe, Delta Lake, fastparquet);
- Ray;
- Prefect's declared Python support;
- `scripts/check_cp315_wheels.py` for the current wheel picture.

## 5. Classification rules (unchanged)

Runtime success and declared upstream support are separate signals. If package
metadata excludes Python 3.15, classify `INCOMPAT` even if import smoke tests
pass. Wheel availability is separate from runtime compatibility.

## 6. Scaffold, then preflight

```bash
.venv/bin/python scripts/scaffold_release.py --release 3.15.0 --previous 3.15.0rc2 --dry-run
.venv/bin/python scripts/scaffold_release.py --release 3.15.0 --previous 3.15.0rc2
.venv/bin/python scripts/preflight_release.py --release 3.15.0
```

The scaffold writes only checklist/placeholder files, never `manifest.json`.
If preflight reports a dirty worktree or an existing active report, stop. If
the scaffold's placeholder files trip the "existing report" check, resolve per
`reports/3.15.0/RELEASE_CHECKLIST.md`.

## 7. Validate

```bash
PYTHON_BIN=.venv/bin/python bash scripts/validate_all.sh
.venv/bin/python -m pytest tests -q
git diff --check
```

Keep Python incompatibility separate from missing wheels, optional dependencies,
Docker gaps, and declared-support metadata. Start Docker first if you want the
PyArrow/PySpark probes to run instead of SKIP.

## 8. Generate evidence

```bash
.venv/bin/python scripts/generate_report.py --release 3.15.0
.venv/bin/python tools/sync_readiness.py
```

Authoritative artifacts: `manifest.json` and `compatibility_report.md`.
The manifest must satisfy `release == 3.15.0` and `python_runtime == 3.15.0`;
any mismatch invalidates the baseline.

## 9. Compare and document

```bash
.venv/bin/python scripts/compare_reports.py 3.15.0rc2 3.15.0
```

Readiness movement is measured, not forced to improve. A `PASS -> SKIP` from
unavailable Docker is not automatically a Python regression.

Then update `STATUS.md`, `README.md` and `ROADMAP.md` from the manifest (not
from memory), and retire the "Waiting, Python 3.15 GA" rows.

## 10. Final gate

Rerun consolidated validation and the full tests, run `git diff --check`,
review all generated artifacts, open a PR, and wait for CI. Tag
(`python-3.15.0-validation`) only after the reviewed baseline is merged.

The goal is truthful, reproducible compatibility evidence, not a
predetermined readiness score.
