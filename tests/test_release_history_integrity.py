from __future__ import annotations

import json
from pathlib import Path

"""
# ============================================================================
# Author: Dr. Ceasar Jackson Jr.
# Project: Python 3.15 Data Engineering Validation Suite
# File: test_release_history_integrity.py
# Purpose:
#     Validate historical release manifests for integrity, consistency,
#     readiness progression, and package accounting.
#
# Validation:
#     python -m py_compile tests/test_release_history_integrity.py
#     python -m pytest tests/test_release_history_integrity.py -v
#
# Script Standards:
#     - Clear documentation and operational guidance
#     - Strong validation and defensive assertions
#     - Maintainability and readability
#     - Production-quality test coverage
#     - Consistent release artifact verification
# ============================================================================
"""

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


RELEASE_MANIFESTS = [
    REPORTS_DIR / "3.15.0b1" / "manifest.json",
    REPORTS_DIR / "3.15.0b2" / "manifest.json",
    REPORTS_DIR / "3.15.0rc1" / "manifest.json",
    REPORTS_DIR / "3.15.0rc2" / "manifest.json",
    REPORTS_DIR / "v1.8.0" / "manifest.json",
    REPORTS_DIR / "v1.8.1" / "manifest.json",
]

# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# Release Integrity Tests
# ----------------------------------------------------------------------------


def test_release_manifests_exist() -> None:
    """Verify all tracked release manifests exist."""
    for manifest in RELEASE_MANIFESTS:
        assert manifest.exists(), f"Missing manifest: {manifest}"


def test_release_names_are_unique() -> None:
    """Verify release identifiers are unique across history."""
    releases = [load_manifest(p)["release"] for p in RELEASE_MANIFESTS]
    assert len(releases) == len(set(releases))


def test_release_has_required_metadata() -> None:
    """Verify required metadata fields exist in every manifest."""
    required = {
        "project",
        "release",
        "release_type",
        "test_date",
        "packages_tested",
        "production_readiness_pct",
    }

    for manifest in RELEASE_MANIFESTS:
        data = load_manifest(manifest)
        missing = required - set(data)
        assert not missing, f"{manifest} missing: {sorted(missing)}"


def test_readiness_values_valid() -> None:
    """Verify readiness percentages remain within valid bounds."""
    for manifest in RELEASE_MANIFESTS:
        readiness = load_manifest(manifest)["production_readiness_pct"]
        assert 0 <= int(readiness) <= 100


def test_package_totals_match_tested() -> None:
    """Verify package status totals equal packages_tested."""
    for manifest in RELEASE_MANIFESTS:
        data = load_manifest(manifest)

        total = (
            int(data.get("packages_pass", 0))
            + int(data.get("packages_fail", 0))
            + int(data.get("packages_incompat", 0))
            + int(data.get("packages_blocked", 0))
            + int(data.get("packages_skip", 0))
        )

        assert total == int(data["packages_tested"])
