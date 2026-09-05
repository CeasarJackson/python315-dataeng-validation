#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Script Name:
    test_release_progression.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Validate release-to-release readiness progression and report consistency.

Validation:
    python -m py_compile tests/test_release_progression.py
    python -m pytest tests/test_release_progression.py -v
==============================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

# Directories that hold scaffolding or withdrawn results rather than reports.
NON_REPORT_DIRS = {"template", "test", "_quarantine"}


def discover_releases() -> list[str]:
    """Return every release that actually has a report on disk.

    Replaces a hardcoded list that required ``3.15.0rc2`` — scheduled for
    2026-09-01 — to already exist. See the note in
    test_release_history_integrity.discover_release_manifests for why that
    mattered.
    """
    return sorted(
        path.name
        for path in REPORTS_DIR.iterdir()
        if path.is_dir()
        and path.name not in NON_REPORT_DIRS
        and (path / "manifest.json").is_file()
    )


RELEASES = discover_releases()


def load_manifest(release: str) -> dict:
    path = REPORTS_DIR / release / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_releases_discovered() -> None:
    assert RELEASES, f"No release reports found under {REPORTS_DIR}"


def test_readiness_range() -> None:
    for release in RELEASES:
        readiness = load_manifest(release)["production_readiness_pct"]
        assert 0 <= readiness <= 100


def test_package_totals_consistent() -> None:
    for release in RELEASES:
        manifest = load_manifest(release)

        calculated_total = (
            int(manifest["packages_pass"])
            + int(manifest["packages_fail"])
            + int(manifest["packages_incompat"])
            + int(manifest.get("packages_blocked", 0))
            + int(manifest["packages_skip"])
        )

        assert calculated_total == int(manifest["packages_tested"])


# Removed: test_readiness_progression, test_rc2_readiness_greater_than_b2 and
# test_latest_release_has_highest_readiness.
#
# Those asserted that readiness never declines and that 3.15.0rc2 scores
# highest. Both encode an expected narrative rather than a property of the
# data, and in a compatibility lab that inverts the point of the exercise: a
# truthful decline — a package regressing, or an INCOMPAT correctly returning
# to the denominator — became a test failure. Combined with requiring an
# unreleased version's report to exist, the pressure was to adjust the reports
# until the suite went green. See ENV-001 and ENV-002 for what that produced.
#
# Readiness movement is now reported by scripts/compare_reports.py and
# interpreted by a human. It is measured, never enforced.


def test_existing_report_pdfs_not_empty() -> None:
    """Historical PDF artifacts, when present, must remain non-empty.

    Compatibility report generation is authoritative through manifest.json
    and compatibility_report.md. Older release directories may also contain
    formal PDF assessments created by a separate historical workflow.
    """
    for release in RELEASES:
        pdf = REPORTS_DIR / release / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"
        if pdf.exists():
            assert pdf.stat().st_size > 0
