#!/usr/bin/env python3
# ============================================================================
# Name: test_report_completeness.py
# Author: Dr. Ceasar Jackson Jr.
# Project: Python 3.15 Data Engineering Validation Suite
# Purpose:
#   Validate that report directories contain all required release artifacts.
#
# Usage:
#   python -m pytest tests/test_report_completeness.py -v
#
# Validation:
#   python -m py_compile tests/test_report_completeness.py
#   python -m pytest tests/test_report_completeness.py -v
#
# Notes:
#   - Enforces report artifact completeness.
#   - Supports release-quality validation gates.
#   - Follows project testing and documentation standards.
# ============================================================================

"""Report completeness validation tests."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

REQUIRED_FILES = [
    "manifest.json",
    "compatibility_report.md",
    "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf",
]

EXTENDED_REPORTS = [
    REPORTS_DIR / "3.15.0b2",
]

EXTENDED_FILES = [
    "readiness_matrix.md",
    "executive_summary.md",
    "full_readiness_assessment.md",
]


def test_reports_directory_exists() -> None:
    """Reports directory should exist."""
    assert REPORTS_DIR.exists()


RELEASE_DIRS = sorted(
    [
        p
        for p in REPORTS_DIR.iterdir()
        if p.is_dir()
        and (p.name.startswith("3.15.") or p.name.startswith("v"))
        and (p / "manifest.json").exists()
    ],
    key=lambda p: p.name,
)


@pytest.mark.parametrize("report_dir", RELEASE_DIRS)
def test_required_report_files_exist(report_dir: Path) -> None:
    """Every report release should contain core artifacts."""
    for filename in REQUIRED_FILES:
        assert (report_dir / filename).exists(), f"Missing {filename} in {report_dir}"


@pytest.mark.parametrize("report_dir", EXTENDED_REPORTS)
def test_extended_report_files_exist(report_dir: Path) -> None:
    """Modern report releases should contain extended artifacts."""
    for filename in EXTENDED_FILES:
        assert (report_dir / filename).exists(), f"Missing {filename} in {report_dir}"
