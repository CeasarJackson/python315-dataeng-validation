#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_lazy_imports_probes.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    PEP 810 (Python 3.15) can defer module-level imports until first use, which
    would defer an ImportError and make a missing package look healthy. Verify
    that the report generator's package probes give identical answers with lazy
    imports off and forced on (``-X lazy_imports=all``), so a probe can never
    report PASS for a package that is not importable.

Validation:
    python -m py_compile tests/test_lazy_imports_probes.py
    python -m pytest tests/test_lazy_imports_probes.py -v

Notes:
    Runs each mode in a fresh interpreter because the flag is fixed at startup.
    Skipped below Python 3.15, where the flag does not exist.

==============================================================================
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)

# Runs inside the child interpreter. It must print exactly one JSON line.
PROBE_SCRIPT = textwrap.dedent("""
    import importlib.util, json, sys

    spec = importlib.util.spec_from_file_location("generate_report_lazy", sys.argv[1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_version = lambda _package: "pinned"
    print(json.dumps({
        "absent": module.probe_package("no_such_package_lazy_315"),
        "present": module.probe_package("json"),
        "prefect": module._probe_prefect()[0]["status"],
    }))
    """)


def run_probes(mode: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            f"lazy_imports={mode}",
            "-c",
            PROBE_SCRIPT,
            str(GENERATOR_PATH),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(sys.version_info < (3, 15), reason="lazy imports are new in 3.15")
def test_probes_are_identical_with_lazy_imports_forced_on() -> None:
    normal = run_probes("normal")
    forced = run_probes("all")
    assert forced == normal


@pytest.mark.skipif(sys.version_info < (3, 15), reason="lazy imports are new in 3.15")
def test_missing_package_still_fails_eagerly_under_lazy_imports() -> None:
    result = run_probes("all")
    assert result["absent"][0] == "FAIL"
    assert result["absent"][1] == "not installed"
    assert result["present"][0] == "PASS"
