#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Script Name:
    test_manifest_schema.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Validate manifest schema consistency across all report directories.

Validation:
    python -m py_compile tests/test_manifest_schema.py
    python -m pytest tests/test_manifest_schema.py -v
==============================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

REQUIRED_FIELDS = {
    "packages_tested",
    "packages_pass",
    "packages_fail",
    "packages_incompat",
    "packages_blocked",
    "packages_skip",
    "production_readiness_pct",
}


def manifest_paths() -> list[Path]:
    return sorted(
        path
        for path in REPORTS_DIR.glob("*/manifest.json")
        if path.parent.name != "template"
    )


MANIFESTS = manifest_paths()


def test_manifests_exist() -> None:
    assert MANIFESTS, "No manifest.json files found under reports/"


import pytest


@pytest.mark.parametrize("manifest_path", MANIFESTS)
def test_manifest_contains_required_fields(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    missing = REQUIRED_FIELDS - set(manifest)

    assert not missing, f"{manifest_path} missing required fields: {sorted(missing)}"


@pytest.mark.parametrize("manifest_path", MANIFESTS)
def test_manifest_package_totals(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    calculated_total = (
        int(manifest["packages_pass"])
        + int(manifest["packages_fail"])
        + int(manifest["packages_incompat"])
        + int(manifest["packages_blocked"])
        + int(manifest["packages_skip"])
    )

    assert calculated_total == int(
        manifest["packages_tested"]
    ), f"{manifest_path}: package counts do not equal packages_tested"


@pytest.mark.parametrize("manifest_path", MANIFESTS)
def test_manifest_readiness_range(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    readiness = int(manifest["production_readiness_pct"])

    assert (
        0 <= readiness <= 100
    ), f"{manifest_path}: readiness must be between 0 and 100"
