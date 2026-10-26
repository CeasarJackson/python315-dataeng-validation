#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify that scripts/ingest_evidence.py validates evidence strictly, builds
    a reconciled manifest with the same readiness formula as
    tools/sync_readiness.py, never touches the baseline manifest, and is
    deterministic.

Validation:
    python -m py_compile tests/test_ingest_evidence.py
    python -m pytest tests/test_ingest_evidence.py -v
    python -m pytest tests/test_script_headers.py -v

==============================================================================
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from scripts import ingest_evidence as ie
from tools.sync_readiness import calculate_readiness as sync_calculate_readiness

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASE = "3.15.1"
REAL_RELEASE_DIR = PROJECT_ROOT / "reports" / RELEASE


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_baseline() -> dict[str, Any]:
    return {
        "release": "9.9.9",
        "production_readiness_pct": 17,
        "results": {
            "alpha": {"status": "FAIL", "version": "not installed"},
            "beta": {"status": "SKIP", "version": "not installed"},
        },
    }


def synthetic_evidence() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "release": "9.9.9",
        "evidence_date": "2026-01-01",
        "packages": {
            "alpha": {
                "status": "PASS",
                "version": "1.0",
                "evidence_level": "Functional",
                "evidence": "ran a workload",
            },
            "beta": {
                "status": "BLOCKED",
                "version": "2.0",
                "evidence_level": "Resolution",
                "evidence": "resolver failed",
                "reason": "no wheel",
            },
        },
    }


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    """A reports/<release> tree holding copies of the real baseline and evidence."""
    release_dir = tmp_path / "reports" / RELEASE
    release_dir.mkdir(parents=True)
    shutil.copy(REAL_RELEASE_DIR / "manifest.json", release_dir / "manifest.json")
    shutil.copy(REAL_RELEASE_DIR / "evidence.json", release_dir / "evidence.json")
    return tmp_path / "reports"


def run_cli(reports_dir: Path, *extra: str) -> int:
    return ie.main(
        ["--release", RELEASE, "--reports-dir", str(reports_dir), *extra],
        configure_logging=False,
    )


# ----------------------------------------------------------------------------
# Validation rules
# ----------------------------------------------------------------------------


def test_valid_synthetic_evidence_has_no_problems() -> None:
    assert ie.validate_evidence(synthetic_evidence(), synthetic_baseline()) == []


@pytest.mark.parametrize("level", ["Resolution", "Install", "Import"])
def test_pass_below_functional_is_rejected(level: str) -> None:
    evidence = synthetic_evidence()
    evidence["packages"]["alpha"]["evidence_level"] = level
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any("PASS requires evidence_level Functional" in p for p in problems)


@pytest.mark.parametrize("status", ["BLOCKED", "INCOMPAT", "FAIL", "SKIP"])
def test_non_pass_status_requires_reason(status: str) -> None:
    evidence = synthetic_evidence()
    evidence["packages"]["alpha"]["status"] = status
    evidence["packages"]["alpha"].pop("reason", None)
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any("reason is required" in p for p in problems)


def test_unknown_status_is_rejected_with_accepted_values() -> None:
    evidence = synthetic_evidence()
    evidence["packages"]["alpha"]["status"] = "MAYBE"
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any(
        "must be one of PASS, FAIL, INCOMPAT, BLOCKED, SKIP" in p for p in problems
    )


def test_unknown_evidence_level_is_rejected() -> None:
    evidence = synthetic_evidence()
    evidence["packages"]["alpha"]["evidence_level"] = "Vibes"
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any("evidence_level must be one of" in p for p in problems)


def test_baseline_package_missing_from_evidence_is_rejected() -> None:
    evidence = synthetic_evidence()
    del evidence["packages"]["beta"]
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any("missing from evidence" in p and "beta" in p for p in problems)


def test_release_mismatch_is_rejected() -> None:
    evidence = synthetic_evidence()
    evidence["release"] = "1.2.3"
    problems = ie.validate_evidence(evidence, synthetic_baseline())
    assert any("release must match" in p for p in problems)


# ----------------------------------------------------------------------------
# Readiness formula
# ----------------------------------------------------------------------------


def test_readiness_matches_sync_readiness_for_adopted_counts() -> None:
    counts = {"PASS": 15, "FAIL": 0, "INCOMPAT": 0, "BLOCKED": 2, "SKIP": 0}
    manifest = {
        "packages_pass": 15,
        "packages_fail": 0,
        "packages_incompat": 0,
        "packages_blocked": 2,
        "packages_skip": 0,
    }
    assert ie.calculate_readiness(counts) == sync_calculate_readiness(manifest) == 94


@pytest.mark.parametrize(
    "counts",
    [
        {"PASS": 1, "FAIL": 9, "INCOMPAT": 0, "BLOCKED": 2, "SKIP": 5},
        {"PASS": 12, "FAIL": 0, "INCOMPAT": 2, "BLOCKED": 2, "SKIP": 1},
        {"PASS": 0, "FAIL": 0, "INCOMPAT": 0, "BLOCKED": 0, "SKIP": 4},
        {"PASS": 3, "FAIL": 1, "INCOMPAT": 1, "BLOCKED": 1, "SKIP": 0},
    ],
)
def test_readiness_parity_with_sync_readiness(counts: dict[str, int]) -> None:
    manifest = {
        "packages_pass": counts["PASS"],
        "packages_fail": counts["FAIL"],
        "packages_incompat": counts["INCOMPAT"],
        "packages_blocked": counts["BLOCKED"],
        "packages_skip": counts["SKIP"],
    }
    assert ie.calculate_readiness(counts) == sync_calculate_readiness(manifest)


# ----------------------------------------------------------------------------
# Real evidence and end-to-end behaviour
# ----------------------------------------------------------------------------


def test_real_evidence_is_valid_and_scores_94() -> None:
    baseline = ie.load_json(REAL_RELEASE_DIR / "manifest.json", "baseline")
    evidence = ie.load_json(REAL_RELEASE_DIR / "evidence.json", "evidence")
    assert ie.validate_evidence(evidence, baseline) == []

    manifest = ie.build_manifest(
        baseline,
        evidence,
        baseline_name="manifest.json",
        baseline_sha256="x",
        evidence_name="evidence.json",
        evidence_sha256="y",
    )
    assert manifest["production_readiness_pct"] == 94, (
        "evidence.json no longer reproduces the adopted 94% in "
        "READINESS_RECONCILIATION_2026-10-26_v2.md"
    )
    assert manifest["packages_tested"] == 17
    assert manifest["packages_pass"] == 15
    assert manifest["packages_blocked"] == 2


def test_build_manifest_does_not_mutate_baseline() -> None:
    baseline = ie.load_json(REAL_RELEASE_DIR / "manifest.json", "baseline")
    before = copy.deepcopy(baseline)
    evidence = ie.load_json(REAL_RELEASE_DIR / "evidence.json", "evidence")
    ie.build_manifest(
        baseline,
        evidence,
        baseline_name="m",
        baseline_sha256="x",
        evidence_name="e",
        evidence_sha256="y",
    )
    assert baseline == before


def test_run_writes_outputs_and_leaves_baseline_untouched(workdir: Path) -> None:
    release_dir = workdir / RELEASE
    baseline_hash = sha(release_dir / "manifest.json")

    assert run_cli(workdir) == 0

    manifest = json.loads((release_dir / ie.DEFAULT_MANIFEST_NAME).read_text())
    assert manifest["production_readiness_pct"] == 94
    assert (release_dir / ie.DEFAULT_COMPARISON_NAME).read_text().strip()
    assert sha(release_dir / "manifest.json") == baseline_hash


def test_reconciled_manifest_satisfies_schema_and_totals(workdir: Path) -> None:
    assert run_cli(workdir) == 0
    manifest = json.loads((workdir / RELEASE / ie.DEFAULT_MANIFEST_NAME).read_text())

    required = {
        "packages_tested",
        "packages_pass",
        "packages_fail",
        "packages_incompat",
        "packages_blocked",
        "packages_skip",
        "production_readiness_pct",
    }
    assert required <= set(manifest)
    total = sum(
        manifest[k]
        for k in (
            "packages_pass",
            "packages_fail",
            "packages_incompat",
            "packages_blocked",
            "packages_skip",
        )
    )
    assert total == manifest["packages_tested"]
    assert manifest["reconciliation"]["baseline_production_readiness_pct"] == 17


def test_dry_run_writes_nothing(workdir: Path) -> None:
    assert run_cli(workdir, "--dry-run") == 0
    assert not (workdir / RELEASE / ie.DEFAULT_MANIFEST_NAME).exists()
    assert not (workdir / RELEASE / ie.DEFAULT_COMPARISON_NAME).exists()


def test_existing_outputs_require_force(workdir: Path) -> None:
    assert run_cli(workdir) == 0
    assert run_cli(workdir) == 1
    assert run_cli(workdir, "--force") == 0


def test_outputs_are_deterministic(workdir: Path) -> None:
    release_dir = workdir / RELEASE
    assert run_cli(workdir) == 0
    first = [
        (release_dir / ie.DEFAULT_MANIFEST_NAME).read_bytes(),
        (release_dir / ie.DEFAULT_COMPARISON_NAME).read_bytes(),
    ]
    assert run_cli(workdir, "--force") == 0
    second = [
        (release_dir / ie.DEFAULT_MANIFEST_NAME).read_bytes(),
        (release_dir / ie.DEFAULT_COMPARISON_NAME).read_bytes(),
    ]
    assert first == second


def test_refuses_to_overwrite_baseline_or_any_manifest_json(workdir: Path) -> None:
    release_dir = workdir / RELEASE
    baseline_hash = sha(release_dir / "manifest.json")

    assert (
        run_cli(
            workdir, "--force", "--out-manifest", str(release_dir / "manifest.json")
        )
        == 1
    )
    assert (
        run_cli(
            workdir,
            "--force",
            "--out-manifest",
            str(release_dir / "other" / "manifest.json"),
        )
        == 1
    )
    assert sha(release_dir / "manifest.json") == baseline_hash


def test_invalid_evidence_exits_nonzero_and_writes_nothing(workdir: Path) -> None:
    release_dir = workdir / RELEASE
    evidence = json.loads((release_dir / "evidence.json").read_text())
    evidence["packages"]["numpy"]["evidence_level"] = "Import"
    (release_dir / "evidence.json").write_text(json.dumps(evidence))

    assert run_cli(workdir) == 1
    assert not (release_dir / ie.DEFAULT_MANIFEST_NAME).exists()


def test_evidence_covers_every_baseline_package() -> None:
    """Drift guard: a package added to the baseline must be added to evidence."""
    baseline = ie.load_json(REAL_RELEASE_DIR / "manifest.json", "baseline")
    evidence = ie.load_json(REAL_RELEASE_DIR / "evidence.json", "evidence")
    assert set(baseline["results"]) <= set(evidence["packages"])


def test_classify_change() -> None:
    assert ie.classify_change("FAIL", "PASS") == "improvement"
    assert ie.classify_change("BLOCKED", "PASS") == "improvement"
    assert ie.classify_change("PASS", "FAIL") == "regression"
    assert ie.classify_change("SKIP", "PASS") == "coverage"
    assert ie.classify_change("SKIP", "BLOCKED") == "coverage"
    assert ie.classify_change("PASS", "PASS") == "unchanged"
