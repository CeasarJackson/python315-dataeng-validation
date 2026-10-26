#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_check_cp315_wheels.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify that check_cp315_wheels separates "pip says no wheel exists" (a real
    BLOCKED result) from "pip could not run" (a tooling failure). Before this was
    pinned, an interpreter without pip reported all 17 packages as BLOCKED.

Validation:
    python -m py_compile tests/test_check_cp315_wheels.py
    python -m pytest tests/test_check_cp315_wheels.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import itertools
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_counter = itertools.count()


def load_checker(monkeypatch, tmp_path) -> ModuleType:
    """Load the script with its log directory redirected away from the repo."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import logger as shared  # the script's own import

    monkeypatch.setattr(shared, "_LOGS_DIR", tmp_path / "logs")
    name = f"check_cp315_wheels_t{next(_counter)}"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "check_cp315_wheels.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # A @dataclass resolves its string annotations through sys.modules[cls.__module__],
    # so the module must be registered before it executes.
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(["pip"], returncode, stdout, stderr)


def test_native_wheel_is_classified_native(monkeypatch, tmp_path) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    wheel = "numpy-2.5.4-cp315-cp315-macosx_11_0_arm64.whl"
    monkeypatch.setattr(
        checker.subprocess, "run", lambda *a, **k: completed(stdout=f"Saved ./{wheel}")
    )
    result = checker.probe("numpy", ["macosx_11_0_arm64"], "3.15", "cp315")
    assert (result.kind, result.wheel) == (checker.NATIVE, wheel)


@pytest.mark.parametrize(
    ("wheel", "kind"),
    [
        ("x-1-cp311-abi3-macosx_11_0_arm64.whl", "abi3"),
        ("x-1-py3-none-any.whl", "pure"),
        ("x-1-cp315-cp315-macosx_11_0_arm64.whl", "native"),
    ],
)
def test_classification_reads_the_abi_tag(monkeypatch, tmp_path, wheel, kind) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    assert checker._classify(wheel, "cp315") == kind


def test_sweep_takes_first_platform_that_resolves(monkeypatch, tmp_path) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    miss = completed(1, stderr="ERROR: No matching distribution found for scipy")
    hit = completed(stdout="Saved ./scipy-1-cp315-cp315-macosx_12_0_arm64.whl")
    answers = iter([miss, hit])
    monkeypatch.setattr(checker.subprocess, "run", lambda *a, **k: next(answers))
    result = checker.probe(
        "scipy", ["macosx_11_0_arm64", "macosx_12_0_arm64"], "3.15", "cp315"
    )
    assert result.platform == "macosx_12_0_arm64"
    assert result.kind == checker.NATIVE


def test_genuine_no_wheel_is_blocked(monkeypatch, tmp_path) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    miss = completed(
        1, stderr="ERROR: Could not find a version that satisfies the requirement ray"
    )
    monkeypatch.setattr(checker.subprocess, "run", lambda *a, **k: miss)
    result = checker.probe(
        "ray", ["macosx_11_0_arm64", "macosx_12_0_arm64"], "3.15", "cp315"
    )
    assert result.blocked
    assert result.wheel is None


@pytest.mark.parametrize(
    "stderr",
    [
        "/venv/bin/python: No module named pip",
        "WARNING: Retrying ... NewConnectionError\nERROR: Could not fetch URL https://pypi.org",
        "",
    ],
    ids=["no-pip", "offline", "silent-failure"],
)
def test_tooling_failure_is_an_error_not_a_blocker(
    monkeypatch, tmp_path, stderr
) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    monkeypatch.setattr(
        checker.subprocess, "run", lambda *a, **k: completed(1, stderr=stderr)
    )
    with pytest.raises(checker.ProbeError):
        checker.probe("numpy", ["macosx_11_0_arm64"], "3.15", "cp315")


def test_main_exits_3_without_probing_when_pip_is_missing(
    monkeypatch, tmp_path
) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(cmd)
        return completed(1, stderr=f"{sys.executable}: No module named pip")

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    assert checker.main(["--packages", "numpy", "ray"]) == 3
    assert len(calls) == 1  # only the pip --version preflight, no per-package probes


def test_main_exit_codes_for_blocked_and_clean(monkeypatch, tmp_path) -> None:
    checker = load_checker(monkeypatch, tmp_path)
    ok = completed(stdout="Saved ./a-1-py3-none-any.whl")
    monkeypatch.setattr(checker.subprocess, "run", lambda *a, **k: ok)
    assert checker.main(["--packages", "a", "--platforms", "macosx_11_0_arm64"]) == 0

    def fake_run(cmd, *args, **kwargs):
        if "--version" in cmd:
            return completed(stdout="pip 26.2.2")
        return completed(1, stderr="ERROR: No matching distribution found for ray")

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    assert checker.main(["--packages", "ray", "--platforms", "macosx_11_0_arm64"]) == 1
