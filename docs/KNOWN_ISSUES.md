# Known Issues

**Project:** Python 3.15 Compatibility Validation Lab
**Last updated:** 2026-10-02 (Python 3.15.0rc2 cycle)

> **rc2 summary.** Reconciliation on 2026-10-02 confirms the valid
> Python 3.15.0rc2 manifest at **82% readiness**: PASS=10, INCOMPAT=2,
> BLOCKED=2, SKIP=3, FAIL=0. Prefect remains INCOMPAT because 3.7.7
> declares Python `<3.15`; functional flow execution additionally exposes
> the Python 3.15 incompatibility documented in PRE-001. PyArrow remains
> BLOCKED after a binary-only resolver probe found no usable `cp315` wheel.
>
> **Historical rc1 summary.** No `cp315` wheels had landed for any blocked package.
> Verified against the PyPI JSON API and the Fedora wheel tracker on 2026-08-05:
> pandas 3.0.5, numpy 2.5.1, pyarrow 25.0.0, ray 2.56.1, scipy 1.18.0 and
> duckdb 1.5.5 all top out at `cp314`; polars 1.43.2 ships a pure-`py3` wheel.
> The entire compiled scientific stack still builds from sdist on 3.15.
> Readiness held at **77%**, unchanged from b4, with every package result
> identical. See RPT-001 for two invalid rc1 reports produced before a valid
> one was obtained.

---

# SCI-001

## Title

SciPy Build Failure on Python 3.15

## Status

OPEN

## Severity

HIGH

## Affected Versions

- Python 3.15.0b2

## Error

```text
TypeError:
ast.Compare.__init__ missing 1 required positional argument: 'left'
```

## Notes

Error text above was captured during the 3.15.0b2 cycle and may be truncated.
Re-verify against 3.15.0rc1 and capture the full traceback before triage.

---

# PD-001

## Title

pandas Requires Manual Build Toolchain (No cp315 Wheels)

## Status

WORKAROUND AVAILABLE

## Severity

MEDIUM

## Affected Versions

- Python 3.15.0b4
- Python 3.15.0rc1 (re-verified 2026-08-05 — still no `cp315` wheels)

## Summary

pandas is **source-compatible** with Python 3.15 — it compiles and passes.
The issue is purely packaging: no `cp315` wheels are published on PyPI, and
pandas' nightly CI matrix tops out at `cp314` / `cp314t`, so no pre-built
artifact exists for 3.15 through any channel.

`uv pip sync` therefore falls back to an sdist build, which fails because the
meson build backend cannot find a `cython` / `cython3` executable inside the
isolated build environment.

## Error

```text
../meson.build:2:0: ERROR: Unknown compiler(s): [['cython'], ['cython3']]
Running `cython3 -V` gave "[Errno 2] No such file or directory: 'cython3'"
```

Attempting `--no-build-isolation` without the full toolchain produces a
second, distinct failure:

```text
ModuleNotFoundError: No module named 'mesonpy'
```

## Workaround

Install the complete build toolchain, then build with isolation disabled:

```bash
uv pip install cython meson-python meson ninja versioneer numpy
uv pip install --no-build-isolation --no-cache pandas==3.0.3
```

Build time is approximately 30 seconds on Apple Silicon. Pinned toolchain
versions are tracked in `requirements-py315-build.txt`.

**Important:** use `uv pip install -r` rather than `uv pip sync` for the
remaining requirements. `sync` enforces the requirements file exactly and will
uninstall the build toolchain, breaking subsequent rebuilds.

## Resolution Criteria

Close when pandas publishes `cp315` wheels to PyPI.

**rc1 re-check (2026-08-05):** not resolved. pandas 3.0.5 still publishes no
`cp315` wheel. The workaround was exercised end-to-end on a genuine 3.15.0rc1
interpreter and succeeded — pandas 3.0.3 built from sdist and probed PASS, as
did duckdb and matplotlib. The RC phase did **not** bring a wheel, contrary to
the expectation recorded above. Next re-check: 3.15.0rc2 (2026-09-01), then
3.15.0 final (2026-10-01). The rc1 release notes explicitly ask maintainers to
publish 3.15 wheels during this phase and confirm that wheels built against an
RC remain valid for the final release, so the window is open.

---

# ARW-001

## Title

pyarrow Unavailable on Python 3.15

## Status

BLOCKED

## Severity

HIGH

## Affected Versions

- Python 3.15.0b4
- Python 3.15.0rc1 (re-verified 2026-08-05 — pyarrow 25.0.0, still `cp314` max)
- Python 3.15.0rc2 (re-verified 2026-10-02 — binary-only resolver probe
  found no usable `cp315` wheel)

## Summary

No usable `cp315` wheel is available in the validated environment. On
2026-10-02, a binary-only `uv` resolver probe against CPython 3.15.0rc2
failed because no compatible `cp315` wheel could be selected. Unlike PD-001,
the previously tested source-build path is not viable: it fails during CMake
configuration rather than at a missing Python-level build dependency, so no
local toolchain fix has been validated.

Validation for pyarrow currently runs through the Docker image
`pyarrow-dataeng:py314` (see `docker/pyarrow_lab/Dockerfile`), which pins
Python 3.14 and does not exercise 3.15.

## Resolution Criteria

Close when Arrow publishes `cp315` wheels. No local workaround available.

---

# RAY-001

## Title

ray Unavailable on Python 3.15

## Status

BLOCKED

## Severity

LOW

## Affected Versions

- Python 3.15.0b4
- Python 3.15.0rc1 (re-verified 2026-08-05 — ray 2.56.1, still `cp314` max)

## Summary

No `cp315` wheels published on PyPI. Not on the critical path for the core
data-engineering stack.

## Resolution Criteria

Close when Ray publishes `cp315` wheels.

---

# ENV-001

## Title

Extended Stack Not Pinned — Validation Coverage Lost on Venv Rebuild

## Status

RESOLVED (pinned 2026-07-21) — historical reports remain affected

## Severity

HIGH

## Affected Versions

- Python 3.15.0b4 (report generated 2026-07-21)

## Summary

Five extended-stack packages were exercised during the 3.15.0b2 cycle but were
installed ad hoc and never recorded in any requirements file. Rebuilding the
virtual environment for 3.15.0b4 silently dropped them.

They did not fail — they stopped being measured:

| Package | 3.15.0b2 | 3.15.0b4 |
|---------|----------|----------|
| apache-airflow 3.2.2 | PASS | SKIP (not installed) |
| dask.dataframe 2026.3.0 | **INCOMPAT** | SKIP (not installed) |
| mlflow 2.16.2 | PASS | SKIP (not installed) |
| prefect 3.7.3 | PASS | SKIP (not installed) |
| pyspark 4.1.2 | PASS | SKIP (Docker image unavailable) |

## Impact — Reported Readiness Was Inflated

`compare_reports.py` showed readiness rising 84% → 88% between b2 and b4. That
movement is an artifact of the scoring model, not real progress.

INCOMPAT counts against the readiness denominator; SKIP does not. When dask
dropped out of the environment, its known incompatibility stopped being
counted, and the score rose despite nothing being fixed.

The b4 figure of 88% should not be cited without this caveat. Regenerate the
report with the extended stack installed to obtain a comparable number, which
is expected to land **below** 88% once dask's INCOMPAT status returns.

Related: pandas was already PASS at 3.0.3 in the b2 report. The 3.15.0b4
toolchain work (PD-001) restored a capability the b2 environment already had
rather than establishing a new one — though it documented the build procedure,
which had not previously been captured.

## Resolution

Extended packages are now pinned in `requirements-py315-dataeng-extended.txt`.
Note that the pinned versions are NOT the b2-recorded versions — those proved
mutually unsatisfiable (see ENV-002). Install order:

```bash
uv pip install -r requirements-py315-build.txt
uv pip install -r requirements-py315-dataeng-jupyter.txt
uv pip install -r requirements-py315-dataeng-extended.txt
```

`pyarrow` and `ray` are deliberately excluded — see ARW-001 and RAY-001.

## Follow-up

- Regenerate the 3.15.0b4 report with the extended stack present.
- Treat any SKIP "not installed" in a future report as an environment defect
  to investigate, not a neutral result.

---

# ENV-002

## Title

3.15.0b2 Environment Was Internally Inconsistent — Historical Results Suspect

## Status

OPEN

## Severity

HIGH

## Affected Versions

- Python 3.15.0b2 (report dated 2026-07-13)

## Summary

Attempting to reinstall the extended stack at the versions recorded in
`reports/3.15.0b2/manifest.json` fails to resolve. The pins are mutually
unsatisfiable:

```text
apache-airflow==3.2.2
  └─ apache-airflow-task-sdk==1.2.2 -> packaging>=25.0

mlflow==2.16.2
  └─ mlflow-skinny==2.16.2          -> packaging<25
```

No value of `packaging` satisfies both. uv refuses the resolution outright:

```text
× No solution found when resolving dependencies:
  ╰─▶ ... we can conclude that apache-airflow==3.2.2 and mlflow==2.16.2
      are incompatible.
```

## Impact

The b2 manifest records **both** packages as PASS. Since no resolver could
have produced that combination, the b2 environment must have been assembled by
incremental ad-hoc installs in which a later install overwrote `packaging` and
left the earlier package's constraint violated.

At least one of `apache-airflow` or `mlflow` was therefore exercised against a
dependency version it does not declare support for. Its PASS result is not
trustworthy, and the **84% b2 readiness baseline is itself suspect** — which
also undermines the b2 → b4 delta reported by `compare_reports.py`.

This is a measurement-integrity defect, not a Python 3.15 compatibility issue.
Nothing here indicates a problem with the interpreter.

## Resolution

`requirements-py315-dataeng-extended.txt` now pins a mutually consistent set
resolved against Python 3.15 on 2026-07-21:

| Package | b2 (inconsistent) | Now (resolved) |
|---------|-------------------|----------------|
| apache-airflow | 3.2.2 | 3.3.0 |
| dask | 2026.3.0 | 2026.7.1 |
| mlflow | 2.16.2 | 3.14.0 |
| prefect | 3.7.3 | 3.7.7 |
| pyspark | 4.1.2 | 4.2.0 |

Note the mlflow major-version jump (2.x → 3.x), which may change behaviour
independently of the interpreter. Treat the next extended-stack result as a
fresh baseline rather than a continuation of the b2 series.

## Follow-up

- Add `uv pip check` to the validation pipeline so constraint violations fail
  loudly instead of being recorded as PASS.
- Have `generate_report.py` record resolver consistency in the manifest.
- Annotate `reports/3.15.0b2/` to note that its extended-stack results are
  not reproducible.

---

# MLF-001

## Title

mlflow Requires pandas<3 — Cannot Coexist With Pinned Core Stack

## Status

OPEN

## Severity

MEDIUM

## Affected Versions

- Python 3.15.0b4 (all mlflow 2.x and 3.x releases)

## Summary

mlflow cannot be installed alongside the pinned core stack. Every current
release constrains `pandas<3`, while the core stack pins `pandas==3.0.3`:

```text
× No solution found when resolving dependencies:
  ╰─▶ Because mlflow==3.14.0 depends on pandas<3 and you require
      mlflow==3.14.0, we can conclude that you require pandas<3.
      And because you require pandas==3.0.3, we can conclude that your
      requirements are unsatisfiable.
```

The only mlflow release that resolves against pandas 3.x is **1.27.0** (2022),
which predates the constraint rather than supporting pandas 3. It is not a
viable target.

## Observed Failure Mode

When mlflow was included in `requirements-py315-dataeng-extended.txt`, uv
attempted to satisfy it by **downgrading pandas 3.0.3 → 2.3.3**. That build
then failed on the PD-001 cython issue, and the entire install transaction
rolled back — silently taking `apache-airflow`, `dask` and `prefect` with it.

This is why the 3.15.0b4 extended stack showed no change after the first
install attempt: nothing was installed at all.

## Important Distinction

This is **not** a Python 3.15 incompatibility. mlflow's constraint is against
**pandas 3.x** and would apply identically on Python 3.12. It must not be
reported as a 3.15 blocker.

## Resolution

mlflow is excluded from `requirements-py315-dataeng-extended.txt`. To validate
it, use a dedicated environment with pandas 2.x:

```bash
uv venv .venv-mlflow --python 3.15
uv pip install --python .venv-mlflow mlflow==3.14.0
```

Report the result as a separate line item; do not merge it into the main
manifest, since the pandas version differs from the core stack.

## Resolution Criteria

Close when mlflow relaxes its constraint to permit pandas 3.x.

---

# PYO3-001

## Title

PyO3 0.26.0 Hard-Caps at Python 3.14 — Blocks Rust-Backed Packages on 3.15

## Status

OPEN

## Severity

CRITICAL

## Affected Versions

- Python 3.15.0b4

## Summary

**This is the first confirmed genuine Python 3.15 incompatibility found by this
lab.** All prior findings (PD-001, ARW-001, RAY-001, MLF-001) were packaging or
dependency-constraint problems. This one is a build-time refusal in compiled
Rust extension code.

PyO3 0.26.0 performs an explicit interpreter-version check in its build script
and aborts when the target is newer than 3.14:

```text
error: the configured Python interpreter version (3.15) is newer than
       PyO3's maximum supported version (3.14)
  = help: please check if an updated version of PyO3 is available.
          Current version: 0.26.0
  = help: set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 to suppress this check
          and build anyway using the stable ABI
```

## Dependency Chain

```text
apache-airflow 3.3.0
  └─ apache-airflow-core 3.3.0
       └─ libcst 1.8.6
            └─ pyo3 0.26.0   <-- caps at Python 3.14
```

## Scope — Wider Than Airflow

PyO3 is the standard Rust binding layer for Python extensions. Any package
that depends on a PyO3 version below the 3.15-supporting release, and that has
no `cp315` wheel forcing a source build, will fail identically.

Note that PyO3 0.26.0 already emits `cargo:rustc-check-cfg=cfg(Py_3_15)`, so
3.15 awareness is partially present; the maximum-version gate simply has not
been lifted.

Newer PyO3 releases do support 3.15 — `pydantic-core 2.46.4` is PyO3-based and
built successfully from source on 3.15.0b4 in this same environment. The
blocker is libcst pinning an older PyO3, not PyO3 as a project.

## Observed Failure Mode

uv installs atomically. When the libcst build failed, the entire transaction
rolled back — including `dask` and `prefect`, which had no build problems of
their own. This is why repeated extended-stack installs produced no change in
the report.

**Install extended packages individually** so one failure does not mask
otherwise-successful installs.

## Workaround (Untested)

```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
  uv pip install --no-cache apache-airflow==3.3.0
```

This suppresses the version gate and builds against the stable ABI. It is
explicitly a forward-compatibility escape hatch: the resulting binary is not
validated against 3.15 by PyO3 upstream, so a successful build should be
recorded as a workaround, **not** as a PASS.

## Resolution Criteria

Close when libcst ships a release depending on a PyO3 version that supports
Python 3.15, or when libcst publishes `cp315` wheels.

## Upstream Reporting

This is worth reporting to the libcst project — it is a concrete, reproducible
3.15 blocker with a clear remedy (bump the PyO3 dependency).

---

# PRE-001

## Title

prefect Declares `requires-python <3.15` — Installs but Is Unsupported

## Status

OPEN

## Severity

MEDIUM

## Affected Versions

- Python 3.15.0b4 (prefect 3.7.7)
- Python 3.15.0rc1 (prefect 3.7.7 — `uv pip check` reports the same
  declared-support violation)
- Python 3.15.0rc2 (prefect 3.7.7 — `uv pip check` reports the `<3.15`
  violation; flow execution also fails through beartype 0.22.9)

## Summary

prefect 3.7.7 installs without error on 3.15.0b4, but its metadata explicitly
excludes the interpreter:

```text
The package `prefect` requires Python >=3.10, <3.15,
but `3.15.0b4` is installed
```

uv does not enforce `requires-python` when installing into an existing
virtual environment, so the constraint violation is silent at install time.
It was caught only by `uv pip check`.

## Impact — Do Not Record as PASS

A top-level `import prefect` succeeds under the current 3.15.0rc2
environment, but that is not sufficient evidence of compatibility. Executing
a minimal `@flow` causes Prefect server code to load the transitive dependency
chain `prefect.server -> docket -> py-key-value-aio -> beartype`; beartype
0.22.9 then imports `typing.no_type_check_decorator`, which is absent in
Python 3.15, producing `ImportError`.

Independently of that runtime failure, Prefect 3.7.7 declares Python `<3.15`.
The package must therefore remain **INCOMPAT (declared)** even if a narrower
import probe succeeds.

Record prefect as **INCOMPAT (declared)** rather than PASS. This is the same
class of defect as ENV-002 — a package exercised outside its declared support
envelope and scored as a success.

## Detection

`uv pip check --python .venv/bin/python` catches the declared
`Requires-Python` violation. Runtime flow execution additionally exposes the
beartype incompatibility described above. Together these demonstrate why both
package metadata and functional probes are required; a top-level import alone
is insufficient.

## Resolution Criteria

Close when Prefect's declared Python support admits 3.15 and the validated
Prefect flow-execution path completes successfully without the observed
Python 3.15 compatibility failure.

---

# RPT-001

## Title

Reporting Pipeline Could Mislabel and Was Incentivised To — Two Invalid rc1 Reports

## Status

RESOLVED (2026-08-05)

## Severity

HIGH

## Affected Versions

- Python 3.15.0rc1 (reporting defect; not a 3.15 compatibility issue)

## Summary

The rc1 cycle produced **two invalid reports before a valid one**, by two
different mechanisms. Neither was detected by the suite at the time.

**Invalid report 1 — wrong interpreter (75%).** `uv python install 3.15`
resolved to **3.15.0b4**, because uv embeds its own list of
python-build-standalone downloads and no rc1 build was published there.
Separately, `uv venv --python 3.15` prompted to replace the existing `.venv`,
was declined, and errored — so every later step ran against the unchanged
21 July b4 environment. `uv pip install -r` became a no-op; the only package
that changed in the whole run was a setuptools downgrade. The report was filed
as `3.15.0rc1` with `python_runtime: 3.15.0b4`, and the 77% → 75% decline was
read as a regression when its sole cause was the `pyarrow-dataeng:py314`
Docker image being absent.

**Invalid report 2 — empty environment (27%).** After installing a genuine
rc1 interpreter, `matplotlib==3.10.9` failed to build: its meson script
downloads freetype-2.6.1 over TLS, and the freshly installed python.org
framework build had no CA bundle until `Install Certificates.command` was run.
uv installs atomically, so the failure rolled back all 136 core packages —
the PYO3-001 pattern again. The resulting report showed seven `FAIL
(not installed)` results and nine "regressions", none real.

A third trap: with the core stack rolled back, `pytest` was not in the venv,
so the bare command silently resolved to Homebrew's **Python 3.14** pytest.
Always invoke as `python -m pytest`.

## Root Cause — the Test Suite Rewarded Fabrication

`tests/test_release_progression.py` hardcoded `3.15.0rc2` — scheduled for
2026-09-01 — as a manifest that must exist, and asserted both that readiness
never declines and that rc2 scores highest:

```python
RELEASES = ["3.15.0b1", "3.15.0b2", "3.15.0rc1", "3.15.0rc2"]
assert readiness == sorted(readiness), "Readiness regression detected"
assert highest_release == "3.15.0rc2"
```

`3.15.0b4` — the only real recent report — was not in the list.

The suite could therefore only pass if reports existed for releases that had
not happened, and only if the numbers rose. That is why hand-written
placeholders existed (`release: 3.15.0rc1` carrying `python_runtime:
3.15.0b2`, claiming 89%). For a compatibility lab this inverts the exercise:
a truthful decline was a test failure. ENV-001, ENV-002 and PRE-001 are
downstream symptoms of this incentive.

## Resolution

- `generate_report.py`: `python_build` now comes from `detect_python_build()`,
  which reads the live interpreter, instead of being formatted from
  `--release`. `verify_release_matches_runtime()` aborts before any artifact
  is written when the probed runtime differs from `--release`; override
  requires an explicit `--allow-version-mismatch`.
- `tests/test_release_history_integrity.py` and
  `tests/test_release_progression.py`: release lists are now discovered from
  `reports/*/manifest.json`, excluding `_quarantine`. `3.15.0b4` is covered
  for the first time.
- Deleted `test_readiness_progression`, `test_rc2_readiness_greater_than_b2`
  and `test_latest_release_has_highest_readiness`. Readiness movement is
  reported by `compare_reports.py` and interpreted by a human — measured,
  never enforced.
- Added `test_manifest_release_matches_runtime`, which fails any committed
  manifest whose `release` disagrees with its `python_runtime`.
- Both invalid reports moved to `reports/_quarantine/` with a README.

## Operational Notes

- Always `uv venv --clear`; without it uv leaves the old venv in place and the
  cycle silently re-measures the previous build.
- Always `python -m pytest`, never bare `pytest`.
- After installing a python.org framework build, run
  `/Applications/Python\ 3.15/Install\ Certificates.command` before any
  source build that fetches vendored dependencies.
- Install extended packages individually when a batch fails, so one build
  error does not roll back unrelated packages.

---

## Issue Index

| ID | Component | Status | Severity |
|----|-----------|--------|----------|
| SCI-001 | scipy | OPEN | HIGH |
| PD-001 | pandas | WORKAROUND AVAILABLE (re-verified rc1) | MEDIUM |
| ARW-001 | pyarrow | BLOCKED (re-verified rc2) | HIGH |
| RAY-001 | ray | BLOCKED (re-verified rc1) | LOW |
| ENV-001 | validation env | RESOLVED (pinned) | HIGH |
| ENV-002 | validation env (b2) | OPEN | HIGH |
| MLF-001 | mlflow | OPEN | MEDIUM |
| PYO3-001 | libcst / pyo3 / airflow | OPEN | CRITICAL |
| PRE-001 | prefect | OPEN | MEDIUM |
| RPT-001 | reporting pipeline / test suite | RESOLVED (2026-08-05) | HIGH |
