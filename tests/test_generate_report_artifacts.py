#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_generate_report_artifacts.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Validate report artifact generation outputs and directory structure.

Validation:
    python -m pytest tests/test_generate_report_artifacts.py -v
==============================================================================
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def test_reports_directory_exists() -> None:
    """Reports root directory should exist."""
    assert REPORTS_DIR.exists()
    assert REPORTS_DIR.is_dir()


def test_b2_release_directory_exists() -> None:
    """3.15.0b2 release directory should exist."""
    release_dir = REPORTS_DIR / "3.15.0b2"
    assert release_dir.exists()
    assert release_dir.is_dir()


def test_b2_manifest_exists() -> None:
    """3.15.0b2 manifest should exist."""
    manifest = REPORTS_DIR / "3.15.0b2" / "manifest.json"
    assert manifest.exists()


def test_b2_readiness_matrix_exists() -> None:
    """3.15.0b2 readiness matrix should exist."""
    matrix = REPORTS_DIR / "3.15.0b2" / "readiness_matrix.md"
    assert matrix.exists()


def test_b2_executive_summary_exists() -> None:
    """3.15.0b2 executive summary should exist."""
    summary = REPORTS_DIR / "3.15.0b2" / "executive_summary.md"
    assert summary.exists()


def test_b2_full_assessment_exists() -> None:
    """3.15.0b2 full assessment should exist."""
    assessment = REPORTS_DIR / "3.15.0b2" / "full_readiness_assessment.md"
    assert assessment.exists()


def test_b2_pdf_exists() -> None:
    """3.15.0b2 PDF assessment should exist."""
    pdf = REPORTS_DIR / "3.15.0b2" / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"
    assert pdf.exists()
