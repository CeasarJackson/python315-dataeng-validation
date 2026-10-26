#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : scripts/ingest_evidence.py

Purpose
-------
Turn a machine-readable evidence file (what was actually tested, in which
isolated environment, and how deeply) into a reconciled manifest for a release,
and write a baseline-versus-reconciled comparison for reference.

scripts/generate_report.py probes only the interpreter environment it runs in,
by importing packages. Packages validated in separate isolated environments
(Prefect, MLflow, PySpark, Airflow, Jupyter/Dask) are invisible to it, and an
import is weaker evidence than a workload that ran. This script keeps the
evidence explicit instead: every status carries an evidence level and a
description, and PASS is accepted only at "Functional" level or above.

The historical baseline manifest is never modified. Outputs are new, derived
files written next to it, so tests that glob "manifest.json" and the baseline
readiness history are unaffected. The readiness formula is the same one used by
tools/sync_readiness.py (tests/test_ingest_evidence.py pins the parity).

Security
--------
Reads and writes local JSON and Markdown only. No network access, no
subprocesses, no credentials. Only file names, counts and SHA-256 digests are
logged.

Usage
-----
    python scripts/ingest_evidence.py --release 3.15.1 --dry-run
    python scripts/ingest_evidence.py --release 3.15.1
    python scripts/ingest_evidence.py --release 3.15.1 --force
    python scripts/ingest_evidence.py --help

Exit Codes
----------
0   Success.
1   Validation or operational failure.
2   Invalid command-line usage.
130 User interrupted execution.

Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Ingest validated package evidence, build a reconciled manifest and
        a baseline-versus-reconciled comparison without touching the baseline.
    Validation: python -m py_compile scripts/ingest_evidence.py;
        python -m pytest tests/test_ingest_evidence.py -v
===============================================================================
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

# When run as a script this is the "__main__" logger that scripts/logger.py
# configures; when imported (tests) it has no handlers and stays quiet.
LOG = logging.getLogger(__name__)

SCHEMA_VERSION = 1
VALID_STATUSES = ("PASS", "FAIL", "INCOMPAT", "BLOCKED", "SKIP")
EVIDENCE_LEVELS = ("Resolution", "Install", "Import", "Functional", "Integration")
PASS_MINIMUM_LEVEL = "Functional"

# Same weighting as tools/sync_readiness.py: SKIP is excluded from the
# denominator, BLOCKED counts half, INCOMPAT a quarter, FAIL nothing.
STATUS_WEIGHTS = {"PASS": 1.0, "BLOCKED": 0.5, "INCOMPAT": 0.25, "FAIL": 0.0}

# Ordering used to classify a status change as improvement or regression.
STATUS_RANK = {"PASS": 0, "BLOCKED": 1, "INCOMPAT": 2, "FAIL": 3}

# Baseline fields copied unchanged. They describe the baseline run (system
# Python dependency check, Docker image tag, ...), not the reconciled evidence,
# so the reconciliation block lists them explicitly instead of implying they
# were re-verified.
CARRIED_OVER_FIELDS = (
    "dependency_check",
    "docker_image",
    "environment_consistent",
    "constraint_violations",
)

DEFAULT_MANIFEST_NAME = "manifest.reconciled.json"
DEFAULT_COMPARISON_NAME = "COMPARISON_baseline_vs_reconciled.md"
# Frozen, byte-identical copy of the original run's manifest. The official
# manifest.json may later be promoted to the reconciled data, so the baseline
# must live under a name that is never overwritten.
DEFAULT_BASELINE_NAME = "manifest.baseline.json"


class EvidenceError(ValueError):
    """Raised when evidence or baseline input is missing or invalid."""


# -----------------------------------------------------------------------------
# Loading and validation
# -----------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    """Load a JSON object, converting every failure into an EvidenceError."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvidenceError(f"{label}: cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"{label}: invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvidenceError(f"{label}: {path} must contain a JSON object")
    return data


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_evidence(evidence: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Return a list of problems; an empty list means the evidence is valid.

    Messages name the field, the problem and the accepted values so a failing
    run says exactly what to fix.
    """
    problems: list[str] = []

    if evidence.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version must be {SCHEMA_VERSION}. "
            f"Got {evidence.get('schema_version')!r}."
        )
    if evidence.get("release") != baseline.get("release"):
        problems.append(
            f"release must match the baseline manifest "
            f"({baseline.get('release')!r}). Got {evidence.get('release')!r}."
        )

    packages = evidence.get("packages")
    if not isinstance(packages, dict) or not packages:
        problems.append("'packages' must be a non-empty object keyed by package name.")
        return problems

    # A package present in the baseline but absent from the evidence would be
    # dropped silently from the reconciled manifest and skew the score.
    baseline_results = baseline.get("results") or {}
    missing = sorted(name for name in baseline_results if name not in packages)
    if missing:
        problems.append(
            "packages missing from evidence (the baseline lists them): " f"{missing}"
        )

    minimum_index = EVIDENCE_LEVELS.index(PASS_MINIMUM_LEVEL)
    for name, entry in packages.items():
        where = f"packages.{name}"
        if not isinstance(entry, dict):
            problems.append(f"{where} must be an object.")
            continue

        status = entry.get("status")
        if status not in VALID_STATUSES:
            problems.append(
                f"{where}.status must be one of {', '.join(VALID_STATUSES)}. "
                f"Got {status!r}."
            )
        for field in ("version", "evidence"):
            if not _non_empty_string(entry.get(field)):
                problems.append(f"{where}.{field} must be a non-empty string.")

        level = entry.get("evidence_level")
        if level not in EVIDENCE_LEVELS:
            problems.append(
                f"{where}.evidence_level must be one of "
                f"{', '.join(EVIDENCE_LEVELS)}. Got {level!r}."
            )
        elif status == "PASS" and EVIDENCE_LEVELS.index(level) < minimum_index:
            problems.append(
                f"{where}: PASS requires evidence_level {PASS_MINIMUM_LEVEL} or "
                f"higher. Got {level!r}."
            )

        # Every non-PASS status must say why, matching the baseline manifest.
        if (
            status in VALID_STATUSES
            and status != "PASS"
            and not _non_empty_string(entry.get("reason"))
        ):
            problems.append(f"{where}.reason is required when status is {status}.")

    return problems


# -----------------------------------------------------------------------------
# Readiness calculation (parity with tools/sync_readiness.py)
# -----------------------------------------------------------------------------


def count_statuses(results: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Count packages per status."""
    counts = dict.fromkeys(VALID_STATUSES, 0)
    for details in results.values():
        status = str(details.get("status", "")).upper()
        if status in counts:
            counts[status] += 1
    return counts


def calculate_readiness(counts: dict[str, int]) -> int:
    """Weighted readiness percentage; SKIP is excluded from the denominator."""
    total = sum(counts.values())
    if total == 0:
        return 0
    effective_total = max(total - counts["SKIP"], 1)
    weighted = sum(counts[status] * weight for status, weight in STATUS_WEIGHTS.items())
    return min(round(weighted / effective_total * 100), 100)


# -----------------------------------------------------------------------------
# Building outputs
# -----------------------------------------------------------------------------


def build_manifest(
    baseline: dict[str, Any],
    evidence: dict[str, Any],
    *,
    baseline_name: str,
    baseline_sha256: str,
    evidence_name: str,
    evidence_sha256: str,
) -> dict[str, Any]:
    """Return the reconciled manifest; the baseline dict is not mutated."""
    manifest = copy.deepcopy(baseline)
    baseline_results = baseline.get("results") or {}
    packages = evidence["packages"]

    # Keep the baseline ordering so diffs and comparisons line up, then append
    # any package that only the evidence knows about.
    ordered = [n for n in baseline_results if n in packages]
    ordered += [n for n in packages if n not in baseline_results]

    results: dict[str, dict[str, Any]] = {}
    for name in ordered:
        entry = packages[name]
        item: dict[str, Any] = {"status": entry["status"], "version": entry["version"]}
        for optional in ("reason", "note"):
            if entry.get(optional):
                item[optional] = entry[optional]
        item["evidence_level"] = entry["evidence_level"]
        item["evidence"] = entry["evidence"]
        results[name] = item

    counts = count_statuses(results)
    manifest["results"] = results
    manifest["packages_tested"] = len(results)
    manifest["packages_pass"] = counts["PASS"]
    manifest["packages_fail"] = counts["FAIL"]
    manifest["packages_incompat"] = counts["INCOMPAT"]
    manifest["packages_blocked"] = counts["BLOCKED"]
    manifest["packages_skip"] = counts["SKIP"]
    manifest["production_readiness_pct"] = calculate_readiness(counts)
    manifest["reconciliation"] = {
        "status": "PROVISIONAL - not an official release score",
        "evidence_date": evidence.get("evidence_date"),
        "baseline_manifest": baseline_name,
        "baseline_sha256": baseline_sha256,
        "baseline_production_readiness_pct": baseline.get("production_readiness_pct"),
        "evidence_file": evidence_name,
        "evidence_sha256": evidence_sha256,
        "standard": evidence.get("standard"),
        "carried_over_from_baseline": [f for f in CARRIED_OVER_FIELDS if f in baseline],
        "note": (
            "Carried-over fields describe the baseline run and were not "
            "re-verified by this reconciliation."
        ),
    }
    return manifest


def classify_change(old: str, new: str) -> str:
    """Classify a status change the way scripts/compare_reports.py does."""
    if old == new:
        return "unchanged"
    if "SKIP" in (old, new):
        return "coverage"
    return (
        "improvement"
        if STATUS_RANK.get(new, 9) < STATUS_RANK.get(old, 9)
        else "regression"
    )


def _cell(value: Any) -> str:
    """Make a value safe for a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def build_comparison(
    baseline: dict[str, Any],
    reconciled: dict[str, Any],
    *,
    baseline_name: str,
    reconciled_name: str,
) -> str:
    """Return a deterministic Markdown comparison (no timestamps)."""
    old_results = baseline.get("results") or {}
    new_results = reconciled["results"]
    old_counts = count_statuses(old_results)
    new_counts = count_statuses(new_results)
    release = reconciled.get("release", "?")
    meta = reconciled["reconciliation"]

    rows: list[tuple[str, str, str, str, str, str, str]] = []
    tally = dict.fromkeys(
        ("improvement", "regression", "coverage", "unchanged", "new"), 0
    )
    for name, new in new_results.items():
        old = old_results.get(name)
        if old is None:
            change = "new"
            old_status, old_version = "-", "-"
        else:
            change = classify_change(old.get("status", "?"), new["status"])
            old_status, old_version = old.get("status", "?"), old.get("version", "?")
        tally[change] += 1
        detail = new.get("reason") or new.get("note") or ""
        rows.append(
            (
                name,
                old_status,
                new["status"],
                change,
                f"{old_version} -> {new['version']}",
                new["evidence_level"],
                detail,
            )
        )

    lines = [
        f"# Python {release} - Baseline vs Reconciled",
        "",
        "**Status:** PROVISIONAL - reference comparison, not an official release score",
        f"**Evidence date:** {meta.get('evidence_date')}",
        f"**Baseline:** `{baseline_name}` (unchanged)",
        f"**Reconciled:** `{reconciled_name}`",
        "",
        "## Readiness",
        "",
        f"Baseline **{baseline.get('production_readiness_pct')}%** -> "
        f"reconciled **{reconciled['production_readiness_pct']}%**.",
        "",
        "Formula: round(100 * (PASS + 0.50 * BLOCKED + 0.25 * INCOMPAT) / "
        "(TOTAL - SKIP)). The score is a weighted package-compatibility "
        "indicator, not production readiness.",
        "",
        "| Status | Baseline | Reconciled | Delta |",
        "|---|---:|---:|---:|",
    ]
    for status in VALID_STATUSES:
        delta = new_counts[status] - old_counts[status]
        lines.append(
            f"| {status} | {old_counts[status]} | {new_counts[status]} | {delta:+d} |"
        )
    lines += [
        f"| Total | {sum(old_counts.values())} | {sum(new_counts.values())} | |",
        "",
        "## Changes by kind",
        "",
        "| Kind | Packages |",
        "|---|---:|",
    ]
    for kind in ("improvement", "regression", "coverage", "unchanged", "new"):
        lines.append(f"| {kind} | {tally[kind]} |")
    lines += [
        "",
        "## Package detail",
        "",
        "| Package | Baseline | Reconciled | Change | Version | Evidence level | Reason / note |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
    lines += [
        "",
        "## Standard applied",
        "",
        f"{_cell((meta.get('standard') or {}).get('pass_requires', 'not recorded'))}",
        "",
        "## Integrity",
        "",
        f"- Baseline `{baseline_name}` SHA-256: `{meta['baseline_sha256']}`",
        f"- Evidence `{meta['evidence_file']}` SHA-256: `{meta['evidence_sha256']}`",
        "",
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Output safety and verification
# -----------------------------------------------------------------------------


def check_output_paths(baseline_path: Path, outputs: list[Path], force: bool) -> None:
    """Refuse any write that could damage the baseline or an unrelated file."""
    resolved = [out.resolve() for out in outputs]
    if len(set(resolved)) != len(resolved):
        raise EvidenceError("output paths must be different files.")
    for out in outputs:
        if out.resolve() == baseline_path.resolve():
            raise EvidenceError(f"refusing to write over the baseline manifest: {out}")
        if out.name == "manifest.json":
            raise EvidenceError(
                f"refusing to write {out}: official manifest.json files are "
                "never written by this script."
            )
        if out.exists() and not force:
            raise EvidenceError(
                f"{out} already exists. Re-run with --force to replace this derived file."
            )


def write_text_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same directory, then rename into place.

    A crash mid-write therefore cannot leave a truncated report behind.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(text)
        os.replace(temp_name, path)
    except OSError:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
        raise


def verify_outputs(
    manifest_path: Path,
    comparison_path: Path,
    baseline_path: Path,
    baseline_sha256: str,
) -> list[str]:
    """Re-read what was written and return any inconsistencies found."""
    problems: list[str] = []
    manifest = load_json(manifest_path, "reconciled manifest")
    counts = count_statuses(manifest.get("results") or {})

    expected = {
        "packages_pass": counts["PASS"],
        "packages_fail": counts["FAIL"],
        "packages_incompat": counts["INCOMPAT"],
        "packages_blocked": counts["BLOCKED"],
        "packages_skip": counts["SKIP"],
        "packages_tested": sum(counts.values()),
        "production_readiness_pct": calculate_readiness(counts),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            problems.append(f"{key} is {manifest.get(key)!r}, expected {value!r}")
    if not comparison_path.read_text(encoding="utf-8").strip():
        problems.append("comparison file is empty")
    if sha256_file(baseline_path) != baseline_sha256:
        problems.append("baseline manifest changed during the run")
    return problems


# -----------------------------------------------------------------------------
# Command line
# -----------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a reconciled manifest and a baseline-vs-reconciled comparison "
            "from an evidence file. The baseline manifest is never modified."
        )
    )
    parser.add_argument(
        "--release", required=True, help="Release directory, e.g. 3.15.1"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=REPORTS_DIR,
        help="Reports root (default: reports/)",
    )
    parser.add_argument(
        "--evidence", type=Path, help="Evidence JSON (default: <release>/evidence.json)"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help=f"Baseline manifest (default: <release>/{DEFAULT_BASELINE_NAME})",
    )
    parser.add_argument(
        "--out-manifest", type=Path, help=f"Default: <release>/{DEFAULT_MANIFEST_NAME}"
    )
    parser.add_argument(
        "--out-comparison",
        type=Path,
        help=f"Default: <release>/{DEFAULT_COMPARISON_NAME}",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate and report; write nothing"
    )
    parser.add_argument(
        "--force", action="store_true", help="Replace existing derived outputs"
    )
    return parser.parse_args(argv)


def _configure_logging() -> None:
    """Attach the shared console/file logger from scripts/logger.py."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from logger import get_logger  # noqa: E402

    get_logger(__name__)


def run(args: argparse.Namespace) -> int:
    release_dir = args.reports_dir / args.release
    baseline_path = args.baseline or release_dir / DEFAULT_BASELINE_NAME
    evidence_path = args.evidence or release_dir / "evidence.json"
    manifest_out = args.out_manifest or release_dir / DEFAULT_MANIFEST_NAME
    comparison_out = args.out_comparison or release_dir / DEFAULT_COMPARISON_NAME

    LOG.info("Release %s | dry-run=%s force=%s", args.release, args.dry_run, args.force)
    baseline = load_json(baseline_path, "baseline manifest")
    evidence = load_json(evidence_path, "evidence")
    baseline_sha = sha256_file(baseline_path)
    evidence_sha = sha256_file(evidence_path)
    LOG.info("Baseline %s sha256=%s", baseline_path.name, baseline_sha)
    LOG.info("Evidence %s sha256=%s", evidence_path.name, evidence_sha)

    problems = validate_evidence(evidence, baseline)
    if problems:
        for problem in problems:
            LOG.error("FAIL: %s", problem)
        return 1
    LOG.info("PASS: evidence valid (%d packages)", len(evidence["packages"]))

    reconciled = build_manifest(
        baseline,
        evidence,
        baseline_name=baseline_path.name,
        baseline_sha256=baseline_sha,
        evidence_name=evidence_path.name,
        evidence_sha256=evidence_sha,
    )
    comparison = build_comparison(
        baseline,
        reconciled,
        baseline_name=baseline_path.name,
        reconciled_name=manifest_out.name,
    )
    counts = count_statuses(reconciled["results"])
    LOG.info(
        "Readiness %s%% -> %s%% | PASS=%d BLOCKED=%d INCOMPAT=%d FAIL=%d SKIP=%d",
        baseline.get("production_readiness_pct"),
        reconciled["production_readiness_pct"],
        counts["PASS"],
        counts["BLOCKED"],
        counts["INCOMPAT"],
        counts["FAIL"],
        counts["SKIP"],
    )

    check_output_paths(baseline_path, [manifest_out, comparison_out], args.force)
    if args.dry_run:
        LOG.info("DRY RUN: would write %s", manifest_out)
        LOG.info("DRY RUN: would write %s", comparison_out)
        return 0

    write_text_atomic(
        manifest_out, json.dumps(reconciled, indent=2, ensure_ascii=False) + "\n"
    )
    write_text_atomic(comparison_out, comparison)
    LOG.info("Wrote %s", manifest_out)
    LOG.info("Wrote %s", comparison_out)

    problems = verify_outputs(manifest_out, comparison_out, baseline_path, baseline_sha)
    if problems:
        for problem in problems:
            LOG.error("FAIL: verification: %s", problem)
        return 1
    LOG.info("PASS: outputs verified; baseline manifest unchanged")
    return 0


def main(argv: list[str] | None = None, *, configure_logging: bool = True) -> int:
    args = parse_args(argv)
    if configure_logging:
        _configure_logging()
    try:
        return run(args)
    except EvidenceError as exc:
        LOG.error("FAIL: %s", exc)
        return 1
    except KeyboardInterrupt:
        LOG.warning("Interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
