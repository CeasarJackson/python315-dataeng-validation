#!/usr/bin/env python3
"""
==============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : tests/test_build_assessment_pdf.py

Purpose
-------
Protect PDF readiness reporting against incorrect Docker runtime
classification and misleading readiness sensitivity statements.

Prerequisites
-------------
Python 3.15 validation environment with pytest.
ReportLab is required only for PDF-rendering integration tests.

Usage
-----
    python -m pytest tests/test_build_assessment_pdf.py -v

Validation
----------
    python -m py_compile tests/test_build_assessment_pdf.py
    python -m pytest tests/test_build_assessment_pdf.py -v

Operational Notes
-----------------
- Tests use isolated temporary output paths.
- The committed release manifest is never modified.
- The validated release PDF is never overwritten.
- Runtime classification is checked through the real PDF generator.

Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Validate readiness PDF generation, Docker runtime evidence,
        manifest consistency, and deterministic reporting.
    Validation: python -m pytest tests/test_build_assessment_pdf.py -v
==============================================================================
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "build_assessment_pdf.py"
MANIFEST_PATH = ROOT / "reports" / "3.15.2" / "manifest.json"


def load_generator():
    """Import the actual PDF generator without invoking its CLI."""
    spec = importlib.util.spec_from_file_location(
        "build_assessment_pdf_under_test",
        GENERATOR_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_manifest():
    """Return a private copy of the release manifest."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_docker_sourced_identifies_pyspark():
    """PySpark must be recognized as Docker-sourced evidence."""
    generator = load_generator()
    manifest = load_manifest()

    assert "pyspark" in generator.docker_sourced(manifest)


@pytest.mark.parametrize(
    ("evidence", "expected_match"),
    [
        (
            "Worker interpreter reporting Python 3.15.2",
            True,
        ),
        (
            "worker interpreter reporting Python 3.14.0",
            False,
        ),
        (
            "Docker image python:3.15.2-slim",
            False,
        ),
        (
            "worker interpreter reporting Python 3.15.20",
            False,
        ),
    ],
)
def test_runtime_evidence_cases(evidence, expected_match):
    """The generator's own matcher must accept only the interpreter's report."""
    generator = load_generator()
    manifest = load_manifest()

    # Call the generator's function, not a copy of its regex: a copy would keep
    # passing if the generator's pattern regressed.
    runtime = manifest["python_runtime"]
    assert generator.docker_runtime_verified(evidence, runtime) is expected_match

    manifest["results"]["pyspark"]["evidence"] = evidence
    assert generator.docker_sourced(manifest) == ["pyspark"]


def test_committed_pyspark_evidence_is_runtime_verified():
    """The 3.15.2 manifest's own PySpark evidence must pass the matcher."""
    generator = load_generator()
    manifest = load_manifest()

    recorded = manifest["results"]["pyspark"]["evidence"]
    assert generator.docker_runtime_verified(recorded, manifest["python_runtime"])


def test_pdf_generator_preserves_sensitivity_disclaimer():
    """The sensitivity calculation must be explicitly hypothetical."""
    source = GENERATOR_PATH.read_text(encoding="utf-8")

    assert "Sensitivity analysis only:" in source
    assert "Hypothetically excluding all of them" in source
    assert "regardless of whether their Python runtime was" in source


def test_manifest_readiness_is_consistent():
    """The PDF generator must accept the authoritative release manifest."""
    generator = load_generator()
    manifest = load_manifest()

    generator.check_consistency(manifest)

    assert manifest["production_readiness_pct"] == 94
    assert manifest["packages_pass"] == 15
    assert manifest["packages_blocked"] == 2


def test_pdf_dry_run_does_not_write(tmp_path):
    """A dry run must validate without creating the requested output."""
    output = tmp_path / "dry_run.pdf"

    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR_PATH),
            "--release",
            "3.15.2",
            "--previous",
            "3.15.1",
            "--output",
            str(output),
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not output.exists()
