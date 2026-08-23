from __future__ import annotations

import json
import re
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


# Directories that hold scaffolding or withdrawn results rather than reports.
NON_REPORT_DIRS = {"template", "test", "_quarantine"}


def discover_release_manifests() -> list[Path]:
    """Find every manifest actually present under reports/.

    Deliberately NOT a hardcoded list. The previous version named
    ``3.15.0rc2`` — a release scheduled for 2026-09-01 — as a required
    manifest, which meant the suite could only pass if someone hand-wrote a
    report for a release that had not happened. That is exactly how the
    placeholder manifests (``release: 3.15.0rc1`` carrying
    ``python_runtime: 3.15.0b2``) came to exist. Discovering from disk removes
    the incentive to fabricate data to satisfy a test.
    """
    return sorted(
        path / "manifest.json"
        for path in REPORTS_DIR.iterdir()
        if path.is_dir()
        and path.name not in NON_REPORT_DIRS
        and (path / "manifest.json").is_file()
    )


RELEASE_MANIFESTS = discover_release_manifests()

# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# Release Integrity Tests
# ----------------------------------------------------------------------------


def test_release_manifests_discovered() -> None:
    """Verify reports/ actually contains manifests to validate."""
    assert RELEASE_MANIFESTS, f"No release manifests found under {REPORTS_DIR}"


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


# A full CPython version, e.g. 3.15.0b4 or 3.15.0rc1. Suite-version reports
# (v1.8.0) and rolling labels (3.15) intentionally do not match.
_CPYTHON_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:a|b|rc)?\d*$")


def test_manifest_release_matches_runtime() -> None:
    """A report must be labelled with the interpreter that produced it.

    Guards the defect found on 2026-08-05: a manifest labelled 3.15.0rc1 whose
    probed `python_runtime` was 3.15.0b4, because `uv python install 3.15`
    resolved to the older build and `uv venv` silently declined to replace the
    existing environment. generate_report.py now refuses this at write time;
    this test keeps already-committed reports honest.
    """
    mismatches = []

    for manifest in RELEASE_MANIFESTS:
        data = load_manifest(manifest)
        release = str(data.get("release", ""))
        runtime = data.get("python_runtime")

        # Legacy manifests predate the runtime field; rolling and suite-version
        # labels are not interpreter versions. Neither is a mislabelling.
        if runtime is None or not _CPYTHON_VERSION.match(release):
            continue

        if str(runtime) != release:
            mismatches.append(
                f"{manifest.parent.name}: labelled {release} "
                f"but ran on {runtime}"
            )

    assert not mismatches, "Mislabelled reports:\n" + "\n".join(mismatches)


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
