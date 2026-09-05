#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Validate compatibility-report comparison semantics, including the
    distinction between true compatibility regressions and test-coverage
    changes involving SKIP states.

Validation:
    python -m py_compile tests/test_compare_reports_semantics.py
    python -m pytest tests/test_compare_reports_semantics.py -q

==============================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_reports as compare_reports


def _write_manifest(
    reports: Path,
    release: str,
    *,
    status: str,
    readiness: int,
    reason: str = "",
) -> None:
    release_dir = reports / release
    release_dir.mkdir(parents=True)
    result = {"status": status, "version": "test"}
    if reason:
        result["reason"] = reason
    manifest = {
        "test_date": "2026-09-05",
        "packages_pass": 1 if status == "PASS" else 0,
        "packages_fail": 1 if status == "FAIL" else 0,
        "packages_incompat": 1 if status == "INCOMPAT" else 0,
        "production_readiness_pct": readiness,
        "results": {"pyspark": result},
    }
    (release_dir / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def test_pass_to_skip_is_coverage_change_not_regression(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    reports = tmp_path / "reports"
    _write_manifest(reports, "old", status="PASS", readiness=100)
    _write_manifest(
        reports,
        "new",
        status="SKIP",
        readiness=100,
        reason="Docker image not available",
    )
    monkeypatch.setattr(compare_reports, "REPORTS", reports)

    compare_reports.compare("old", "new", fmt="markdown")
    output = capsys.readouterr().out

    assert "## Coverage Changes" in output
    assert "| pyspark | PASS | SKIP | Docker image not available |" in output
    assert "## Regressions" not in output


def test_pass_to_incompat_remains_regression(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    reports = tmp_path / "reports"
    _write_manifest(reports, "old", status="PASS", readiness=100)
    _write_manifest(
        reports,
        "new",
        status="INCOMPAT",
        readiness=75,
        reason="declared unsupported",
    )
    monkeypatch.setattr(compare_reports, "REPORTS", reports)

    compare_reports.compare("old", "new", fmt="markdown")
    output = capsys.readouterr().out

    assert "## Regressions" in output
    assert "| pyspark | PASS | INCOMPAT | declared unsupported |" in output
