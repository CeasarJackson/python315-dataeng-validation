#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Synchronize readiness calculations, manifests, and report metadata
    across generated Python 3.15 compatibility reports.

Validation:
    python -m py_compile tools/sync_readiness.py
    python -m pytest tests/test_sync_readiness.py -v
    python -m pytest tests/test_script_headers.py -v

==============================================================================
"""

from __future__ import annotations

from pathlib import Path

from tools.sync_readiness import (
    calculate_readiness,
    process_report,
    update_markdown,
)


def test_calculate_readiness_packages_schema() -> None:
    manifest = {
        "packages_pass": 12,
        "packages_incompat": 2,
        "packages_blocked": 2,
        "packages_skip": 1,
        "packages_fail": 0,
    }

    assert calculate_readiness(manifest) == 84


def test_calculate_readiness_results_schema() -> None:
    manifest = {
        "results": {
            "numpy": {"status": "PASS"},
            "ray": {"status": "BLOCKED"},
            "prefect": {"status": "INCOMPAT"},
        }
    }

    assert calculate_readiness(manifest) == 58


def test_update_markdown_already_synchronized(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("Production Readiness: 84%\n", encoding="utf-8")

    assert update_markdown(report, 84, dry_run=False) is True
    assert report.read_text(encoding="utf-8") == "Production Readiness: 84%\n"


def test_update_markdown_without_marker(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("# Compatibility Report\n", encoding="utf-8")

    assert update_markdown(report, 84, dry_run=False) is True
    assert report.read_text(encoding="utf-8") == "# Compatibility Report\n"


def test_process_report_invalid_json(tmp_path: Path) -> None:
    report_dir = tmp_path / "broken"
    report_dir.mkdir()

    (report_dir / "manifest.json").write_text(
        "not valid json",
        encoding="utf-8",
    )

    assert (
        process_report(
            report_dir,
            dry_run=True,
            verbose=True,
        )
        is False
    )
