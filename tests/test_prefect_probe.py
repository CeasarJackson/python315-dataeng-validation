#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_prefect_probe.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify that generate_report._probe_prefect() separates a missing Prefect
    (SKIP) from a Prefect whose import fails (INCOMPAT), so a broken install is
    never reported as "not installed".

Validation:
    python -m py_compile tests/test_prefect_probe.py
    python -m pytest tests/test_prefect_probe.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)


def load_generator() -> ModuleType:
    """Load generate_report.py with a deterministic get_version."""
    spec = importlib.util.spec_from_file_location("generate_report_pp", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_version = lambda _package: "9.9.9"
    return module


def fake_prefect(
    monkeypatch, getattr_error: BaseException | None = None, with_flow=False
):
    """Install a stand-in ``prefect`` module whose ``flow`` lookup raises or works."""
    fake = ModuleType("prefect")
    if with_flow:
        fake.flow = lambda func: func
    elif getattr_error is not None:

        def _raise(name: str):
            raise getattr_error

        fake.__getattr__ = _raise
    monkeypatch.setitem(sys.modules, "prefect", fake)


def test_import_success_is_pass(monkeypatch) -> None:
    fake_prefect(monkeypatch, with_flow=True)
    result, detail = load_generator()._probe_prefect()
    assert result == {"status": "PASS", "version": "9.9.9"}
    assert detail == "9.9.9"


def test_prefect_absent_is_skip(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "prefect", None)  # makes `import prefect` fail
    result, detail = load_generator()._probe_prefect()
    assert result == {"status": "SKIP", "version": "not installed"}
    assert detail == "not installed"


def test_removed_stdlib_name_is_incompat(monkeypatch) -> None:
    error = ImportError("cannot import name 'no_type_check_decorator' from 'typing'")
    fake_prefect(monkeypatch, getattr_error=error)
    result, detail = load_generator()._probe_prefect()
    assert result["status"] == "INCOMPAT"
    assert "no_type_check_decorator" in result["reason"]
    assert detail == "stdlib change"


def test_missing_dependency_is_incompat_not_skip(monkeypatch) -> None:
    """Prefect present, a dependency missing: a broken install, not 'not installed'."""
    error = ModuleNotFoundError("No module named 'beartype'", name="beartype")
    fake_prefect(monkeypatch, getattr_error=error)
    result, _ = load_generator()._probe_prefect()
    assert result["status"] == "INCOMPAT"
    assert result["version"] == "9.9.9"
    assert "beartype" in result["reason"]


def test_other_import_error_is_incompat(monkeypatch) -> None:
    fake_prefect(monkeypatch, getattr_error=ImportError("undefined symbol: foo"))
    result, _ = load_generator()._probe_prefect()
    assert result["status"] == "INCOMPAT"
    assert "undefined symbol" in result["reason"]


@pytest.mark.parametrize("exc", [RuntimeError("boom"), ValueError("bad")])
def test_non_import_exception_is_incompat(monkeypatch, exc) -> None:
    fake_prefect(monkeypatch, getattr_error=exc)
    result, detail = load_generator()._probe_prefect()
    assert result["status"] == "INCOMPAT"
    assert result["reason"] == str(exc)
    assert detail == str(exc)
