# Quarantined Reports

Reports in this directory are **not valid results** and must not be cited,
compared against, or used as a baseline. They are retained only so the record
of how they came to exist is not lost.

---

## `3.15.0rc1-MISLABELED-ran-on-b4`

**Generated:** 2026-08-05 · **Reported readiness:** 75%

Labelled `3.15.0rc1`, but produced by a Python **3.15.0b4** interpreter.

The manifest contradicts itself, which is what exposed the problem:

```json
"python_build":   "cpython-3.15.0rc1-macos-aarch64-none",   // synthesised from --release
"python_runtime": "3.15.0b4",                               // actually probed
```

Two independent causes, both silent:

1. `uv python install 3.15` resolved to **3.15.0b4**. uv embeds its own list of
   available python-build-standalone downloads, and no `3.15.0rc1` macOS ARM64
   build was published there at the time (rc1 was one day old).
2. `uv venv --python 3.15` prompted to replace the existing `.venv` and was
   answered **no**, so it errored out. Every subsequent step ran against the
   unchanged 21 July b4 environment. `uv pip install -r` was effectively a
   no-op — the only package that changed in the entire run was a setuptools
   downgrade (83.0.0 → 82.0.1) pinned by the jupyter requirements.

The reported 77% → 75% decline is therefore **not an rc1 regression**. The sole
delta from the b4 report is `pyspark PASS → SKIP`, caused by the
`pyarrow-dataeng:py314` Docker image not being available on the host. Per the
ENV-001 follow-up rule, that is an environment defect to investigate, not a
neutral result and not a compatibility finding. The other 16 packages are
unchanged.

Corroborating evidence inside the report itself: prefect's INCOMPAT reason
reads *"requires Python >=3.10, <3.15, but `3.15.0b4` is installed."*

**Prevention:** `scripts/generate_report.py` now derives `python_build` from
the live interpreter via `detect_python_build()` and aborts via
`verify_release_matches_runtime()` when the probed runtime does not match
`--release`. Reproducing this failure now requires an explicit
`--allow-version-mismatch`.

---

## `3.15.0rc2-PLACEHOLDER-never-run`

**Created:** 2026-06-05 · **Reported readiness:** speculative

Written two months before rc1 existed and roughly three months before rc2 was
scheduled (2026-09-01, per PEP 790). It records `"python_runtime": "3.15.0b2"`
under an `3.15.0rc2` label — the same defect class as the entry above, but
authored by hand rather than generated.

The since-overwritten `3.15.0rc1` placeholder from the same date shared this
problem: it claimed 89% readiness with 13 PASS against a b2 runtime.

---

## Re-running properly

A genuine rc1 cycle needs a real rc1 interpreter and a clean environment:

```bash
uv self update                      # uv's embedded download list must know rc1
uv python install 3.15.0rc1
uv venv --clear --python 3.15.0rc1  # --clear is essential; without it the
                                    # old venv survives and is re-measured
uv pip install -r requirements-py315-build.txt
uv pip install -r requirements-py315-dataeng-jupyter.txt
source .venv/bin/activate
python -c "import sys; print(sys.version)"   # must print 3.15.0rc1
```

If python-build-standalone still has no rc1 build, install the python.org
macOS installer and point uv at it directly:

```bash
uv venv --clear --python /Library/Frameworks/Python.framework/Versions/3.15/bin/python3.15
```

Restore a quarantined report only if it is later re-validated against the
interpreter named on its label.
