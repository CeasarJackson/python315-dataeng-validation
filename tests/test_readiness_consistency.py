#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_readiness_consistency.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Validate consistency between manifest.json and generated readiness
    artifacts.

Validation:
    python -m py_compile tests/test_readiness_consistency.py
    python -m pytest tests/test_readiness_consistency.py -v

==============================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports" / "3.15.1"

MANIFEST = REPORT_DIR / "manifest.json"
READINESS_JSON = REPORT_DIR / "readiness_matrix.json"
READINESS_MD = REPORT_DIR / "readiness_matrix.md"
EXEC_SUMMARY = REPORT_DIR / "executive_summary.md"
FULL_ASSESSMENT = REPORT_DIR / "full_readiness_assessment.md"
PDF_REPORT = REPORT_DIR / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"


def load_manifest() -> dict:
    """Load manifest.json."""
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_exists() -> None:
    """Manifest should exist."""
    assert MANIFEST.exists()


def test_readiness_range() -> None:
    """Readiness must be between 0 and 100."""
    manifest = load_manifest()

    readiness = manifest["production_readiness_pct"]

    assert isinstance(readiness, int)
    assert 0 <= readiness <= 100


def test_manifest_package_counts() -> None:
    """Package counters should be internally consistent."""
    manifest = load_manifest()

    total = (
        manifest["packages_pass"]
        + manifest["packages_fail"]
        + manifest["packages_incompat"]
        + manifest["packages_blocked"]
        + manifest["packages_skip"]
    )

    assert total == manifest["packages_tested"]


def test_readiness_matrix_json_matches_manifest() -> None:
    """JSON readiness matrix should match manifest readiness."""
    assert READINESS_JSON.exists()

    manifest = load_manifest()

    matrix = json.loads(READINESS_JSON.read_text(encoding="utf-8"))

    assert matrix["production_readiness_pct"] == manifest["production_readiness_pct"]


def test_readiness_matrix_contains_readiness() -> None:
    """Markdown matrix should contain readiness percentage."""
    manifest = load_manifest()

    readiness = str(manifest["production_readiness_pct"])

    text = READINESS_MD.read_text(encoding="utf-8")

    assert readiness in text


def test_executive_summary_contains_readiness() -> None:
    """Executive summary should contain readiness percentage."""
    manifest = load_manifest()

    readiness = str(manifest["production_readiness_pct"])

    text = EXEC_SUMMARY.read_text(encoding="utf-8")

    assert readiness in text


def test_full_assessment_contains_readiness() -> None:
    """Assessment should contain readiness percentage."""
    manifest = load_manifest()

    readiness = str(manifest["production_readiness_pct"])

    text = FULL_ASSESSMENT.read_text(encoding="utf-8")

    assert readiness in text


def test_pdf_exists() -> None:
    """PDF report should exist."""
    assert PDF_REPORT.exists()


def test_pdf_not_empty() -> None:
    """PDF should not be empty."""
    assert PDF_REPORT.stat().st_size > 0


# ---------------------------------------------------------------------------
# Releases that follow the baseline -> evidence -> reconciled -> sync flow.
# The checks above stay pinned to 3.15.1 because that release is published
# with every artifact, including readiness_matrix.json and the PDF. 3.15.2
# does not carry those two yet, so asserting them there would fail for a
# reason unrelated to consistency. The checks below cover what 3.15.2 does
# have, and the parametrization makes adding 3.15.3 a one-line change.
# ---------------------------------------------------------------------------
RECONCILED_RELEASES = ["3.15.1", "3.15.2"]
READINESS_DOCS = [
    "readiness_matrix.md",
    "executive_summary.md",
    "full_readiness_assessment.md",
]


def _load_release_manifest(release: str) -> dict:
    path = PROJECT_ROOT / "reports" / release / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("release", RECONCILED_RELEASES)
def test_release_manifest_counts_are_consistent(release: str) -> None:
    """Counters must sum to packages_tested for every reconciled release."""
    manifest = _load_release_manifest(release)

    total = sum(
        manifest[key]
        for key in (
            "packages_pass",
            "packages_fail",
            "packages_incompat",
            "packages_blocked",
            "packages_skip",
        )
    )

    assert total == manifest["packages_tested"], release


@pytest.mark.parametrize("release", RECONCILED_RELEASES)
@pytest.mark.parametrize("filename", READINESS_DOCS)
def test_release_docs_state_manifest_readiness(release: str, filename: str) -> None:
    """Each readiness document must carry the manifest's exact percentage."""
    manifest = _load_release_manifest(release)
    expected = f"Production Readiness: {manifest['production_readiness_pct']}%"

    text = (PROJECT_ROOT / "reports" / release / filename).read_text(encoding="utf-8")

    assert expected in text, f"{release}/{filename} lacks '{expected}'"
