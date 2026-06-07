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

Validation Commands:
    python -m py_compile tests/test_release_progression.py
    python -m pytest tests/test_release_progression.py -v
==============================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

RELEASES = [
    "3.15.0b1",
    "3.15.0b2",
    "3.15.0rc1",
    "3.15.0rc2",
]


def load_manifest(release: str) -> dict:
    path = REPORTS_DIR / release / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_manifests_exist() -> None:
    for release in RELEASES:
        assert (REPORTS_DIR / release / "manifest.json").exists()


def test_readiness_progression() -> None:
    readiness = [
        load_manifest(release)["production_readiness_pct"] for release in RELEASES
    ]

    assert readiness == sorted(readiness), f"Readiness regression detected: {readiness}"


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
            + int(manifest["packages_blocked"])
            + int(manifest["packages_skip"])
        )

        assert calculated_total == int(manifest["packages_tested"])


def test_rc2_readiness_greater_than_b2() -> None:
    rc2 = load_manifest("3.15.0rc2")["production_readiness_pct"]
    b2 = load_manifest("3.15.0b2")["production_readiness_pct"]

    assert rc2 >= b2


def test_latest_release_has_highest_readiness() -> None:
    readiness = {
        release: load_manifest(release)["production_readiness_pct"]
        for release in RELEASES
    }

    highest_release = max(readiness, key=readiness.get)

    assert highest_release == "3.15.0rc2"


def test_report_pdfs_exist() -> None:
    for release in RELEASES:
        pdf = REPORTS_DIR / release / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"
        assert pdf.exists()
