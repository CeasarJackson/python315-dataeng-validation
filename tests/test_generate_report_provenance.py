#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_generate_report_provenance.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Protect report generation from interpreter-environment leakage and stale
    platform metadata.

Validation:
    python -m py_compile tests/test_generate_report_provenance.py
    python -m pytest tests/test_generate_report_provenance.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_report.py"


def load_generator():
    """Load generate_report.py as an importable test module."""
    spec = importlib.util.spec_from_file_location(
        "generate_report_under_test",
        GENERATOR_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_support_targets_running_interpreter(monkeypatch) -> None:
    """uv pip check must explicitly target the interpreter running the report."""
    generator = load_generator()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(generator.subprocess, "run", fake_run)

    results = {
        "prefect": {
            "status": "PASS",
            "version": "3.7.7",
        }
    }

    violations = generator.check_declared_support(results)

    assert violations == []
    assert captured["cmd"] == [
        "uv",
        "pip",
        "check",
        "--python",
        sys.executable,
    ]


def test_declared_python_constraint_downgrades_pass(monkeypatch) -> None:
    """A package that excludes the runtime must not remain PASS."""
    generator = load_generator()

    output = (
        "Found 1 incompatibility\n"
        "The package `prefect` requires Python >=3.10, <3.15, "
        "but `3.15.0rc2` is installed\n"
    )

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr=output)

    monkeypatch.setattr(generator.subprocess, "run", fake_run)

    results = {
        "prefect": {
            "status": "PASS",
            "version": "3.7.7",
        }
    }

    violations = generator.check_declared_support(results)

    assert len(violations) == 1
    assert results["prefect"]["status"] == "INCOMPAT"
    assert results["prefect"]["version"] == "3.7.7"
    assert "declared unsupported" in results["prefect"]["reason"]


def test_compat_report_uses_live_platform(tmp_path, monkeypatch) -> None:
    """Compatibility Markdown must derive platform data at generation time."""
    generator = load_generator()

    monkeypatch.setattr(generator.platform, "mac_ver", lambda: ("26.6.2", (), ""))
    monkeypatch.setattr(generator.platform, "machine", lambda: "arm64")

    results = {
        "numpy": {"status": "PASS", "version": "2.4.6"},
    }

    counts = {
        "PASS": 1,
        "FAIL": 0,
        "INCOMPAT": 0,
        "BLOCKED": 0,
        "SKIP": 0,
    }

    generator.write_compat_report(
        tmp_path,
        "3.15.0rc2",
        results,
        counts,
    )

    report = (tmp_path / "compatibility_report.md").read_text(encoding="utf-8")

    assert "**Platform:** macOS 26.6.2 arm64" in report
    assert "macOS 26.5 ARM64" not in report


def test_generator_does_not_copy_legacy_root_pdf() -> None:
    """Versioned reports must not silently inherit the legacy root PDF."""
    source = GENERATOR_PATH.read_text(encoding="utf-8")

    assert 'REPO / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"' not in source
    assert "shutil.copy2" not in source


def test_generator_readiness_matches_canonical_weighting() -> None:
    source = Path("scripts/generate_report.py").read_text(encoding="utf-8")

    assert 'counts.get("BLOCKED", 0) * 0.50' in source
    assert 'counts.get("INCOMPAT", 0) * 0.25' in source
    assert "round((_wp / _eff) * 100)" in source
    assert 'counts.get("BLOCKED", 0) * 0.3' not in source
