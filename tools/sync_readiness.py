#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Script Name:
    sync_readiness.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Synchronize production readiness metrics across Python 3.15 readiness
    report artifacts. The manifest.json file is treated as the source of truth,
    and Markdown report files are updated to match the calculated readiness
    percentage.

Usage:
    python tools/sync_readiness.py
    python tools/sync_readiness.py --release 3.15.0b2
    python tools/sync_readiness.py --dry-run
    python tools/sync_readiness.py --verbose

Validation Commands:
    python -m py_compile tools/sync_readiness.py
    python tools/sync_readiness.py --dry-run
    python tools/sync_readiness.py --release 3.15.0b2 --dry-run
    python tools/sync_readiness.py
    jq '.production_readiness_pct' reports/3.15.0b2/manifest.json

Updated Artifacts:
    - manifest.json
    - compatibility_report.md
    - readiness_matrix.md
    - executive_summary.md
    - full_readiness_assessment.md

Operational Notes:
    - Manifest is the single source of truth.
    - Supports current manifests with packages_* counters.
    - Supports manifests with results or validation_results sections.
    - Supports older legacy flat pass/fail/incompat/blocked/skip counters.
    - Reconstructs packages_blocked from results when missing.
    - Missing Markdown files are skipped safely with warnings.
    - Invalid JSON manifests are reported and skipped.
    - Logs are written to logs/sync_readiness.log.

Readiness Formula:
    SKIP entries are excluded from the denominator.
    PASS contributes 1.00.
    BLOCKED contributes 0.50.
    INCOMPAT contributes 0.25.
    FAIL contributes 0.00.

Example:
    PASS=12, BLOCKED=2, INCOMPAT=2, SKIP=1, FAIL=0
    effective_total = 17 - 1 = 16
    weighted_score = 12 + (2 * 0.50) + (2 * 0.25) = 13.5
    readiness = round(13.5 / 16 * 100) = 84

Exit Codes:
    0 = Completed successfully, including warnings.
    1 = Fatal runtime error.

Change Log:
    2026-06-07:
        Restored full script structure after accidental partial patch.
        Added current packages_* manifest support.
        Added results and validation_results support.
        Added colorized console logging and file logging.
        Added dry-run, release filtering, and verbose mode.
==============================================================================
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "sync_readiness.log"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"

MARKDOWN_FILES = [
    "compatibility_report.md",
    "readiness_matrix.md",
    "executive_summary.md",
    "full_readiness_assessment.md",
]


def write_log(level: str, message: str, color: str = NC) -> None:
    """Write a message to both console and the sync readiness log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console_message = f"{color}[{level}]{NC} {message}"
    file_message = f"[{timestamp}] [{level}] {message}"

    print(console_message)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(file_message + "\n")


def log_info(message: str) -> None:
    write_log("INFO", message, BLUE)


def log_success(message: str) -> None:
    write_log("PASS", message, GREEN)


def log_warning(message: str) -> None:
    write_log("WARN", message, YELLOW)


def log_error(message: str) -> None:
    write_log("ERROR", message, RED)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Synchronize production readiness metrics across report artifacts."
    )
    parser.add_argument(
        "--release",
        help="Only synchronize one report directory, for example 3.15.0b2 or v1.8.1.",
    )
    parser.add_argument(
        "--reports-dir",
        default=str(REPORTS_DIR),
        help="Path to reports directory. Defaults to project reports/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate and display updates without writing files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional diagnostic information.",
    )
    return parser.parse_args()


def count_statuses(manifest: dict[str, Any]) -> dict[str, int]:
    """Return PASS/FAIL/INCOMPAT/BLOCKED/SKIP counts from supported schemas."""
    counts = {
        "PASS": 0,
        "FAIL": 0,
        "INCOMPAT": 0,
        "BLOCKED": 0,
        "SKIP": 0,
    }

    results = manifest.get("results") or manifest.get("validation_results") or {}
    if isinstance(results, dict) and results:
        for details in results.values():
            if not isinstance(details, dict):
                continue
            status = str(details.get("status", "")).upper()
            if status in counts:
                counts[status] += 1
        return counts

    if "packages_pass" in manifest:
        counts["PASS"] = int(manifest.get("packages_pass", 0))
        counts["FAIL"] = int(manifest.get("packages_fail", 0))
        counts["INCOMPAT"] = int(manifest.get("packages_incompat", 0))
        counts["BLOCKED"] = int(manifest.get("packages_blocked", 0))
        counts["SKIP"] = int(manifest.get("packages_skip", 0))
        return counts

    counts["PASS"] = int(manifest.get("pass", 0))
    counts["FAIL"] = int(manifest.get("fail", 0))
    counts["INCOMPAT"] = int(manifest.get("incompat", 0))
    counts["BLOCKED"] = int(manifest.get("blocked", 0))
    counts["SKIP"] = int(manifest.get("skip", 0))
    return counts


def calculate_readiness(manifest: dict[str, Any]) -> int:
    """Calculate weighted production readiness from manifest validation results."""
    counts = count_statuses(manifest)

    total = sum(counts.values())
    if total == 0:
        return 0

    effective_total = max(total - counts["SKIP"], 1)
    weighted_score = (
        counts["PASS"] + (counts["BLOCKED"] * 0.50) + (counts["INCOMPAT"] * 0.25)
    )

    readiness = round((weighted_score / effective_total) * 100)
    return min(readiness, 100)


def update_manifest(manifest: dict[str, Any], readiness: int) -> dict[str, Any]:
    """Return an updated manifest with synchronized readiness and counts."""
    counts = count_statuses(manifest)
    updated = dict(manifest)

    updated["packages_pass"] = counts["PASS"]
    updated["packages_fail"] = counts["FAIL"]
    updated["packages_incompat"] = counts["INCOMPAT"]
    updated["packages_blocked"] = counts["BLOCKED"]
    updated["packages_skip"] = counts["SKIP"]
    updated["packages_tested"] = sum(counts.values())
    updated["production_readiness_pct"] = readiness

    return updated


def update_markdown(path: Path, readiness: int, dry_run: bool) -> bool:
    """Synchronize readiness text in a Markdown artifact."""
    if not path.exists():
        log_warning(f"Missing file: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    original = text

    replacements = [
        (
            r"\*\*Overall Readiness Score:\s*\d+%\*\*",
            f"**Overall Readiness Score: {readiness}%**",
        ),
        (
            r"\*\*Overall Readiness:\s*\d+%\*\*",
            f"**Overall Readiness: {readiness}%**",
        ),
        (
            r"\*\*Production Readiness Score:\*\*\s*\d+%",
            f"**Production Readiness Score:** {readiness}%",
        ),
        (
            r"Production Readiness\s*[:=]\s*\d+%",
            f"Production Readiness: {readiness}%",
        ),
        (
            r"Production Readiness Percentage\s*[:=]\s*\d+%",
            f"Production Readiness Percentage: {readiness}%",
        ),
        (
            r"production_readiness_pct\s*[:=]\s*\d+",
            f"production_readiness_pct: {readiness}",
        ),
        (
            r"\| Production Readiness \(%\) \| \d+ \|",
            f"| Production Readiness (%) | {readiness} |",
        ),
    ]

    matched_pattern = False

    for pattern, _replacement in replacements:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matched_pattern = True
            break

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    if not matched_pattern:
        log_info(
            f"No recognized readiness markers found in: {path}"
        )
        return True

    if text == original:
        log_info(
            f"Readiness already synchronized (no changes required): {path}"
        )
        return True

    if dry_run:
        log_info(f"Dry run: would update {path}")
        return True

    path.write_text(text, encoding="utf-8")
    log_success(f"Updated Markdown readiness: {path}")
    return True


def process_report(report_dir: Path, dry_run: bool, verbose: bool) -> bool:
    """Process one report directory."""
    manifest_path = report_dir / "manifest.json"

    if not manifest_path.exists():
        if verbose:
            log_warning(f"Skipping directory without manifest: {report_dir}")
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log_error(f"Invalid JSON manifest skipped: {manifest_path}: {exc}")
        return False
    except OSError as exc:
        log_error(f"Unable to read manifest: {manifest_path}: {exc}")
        return False

    readiness = calculate_readiness(manifest)
    counts = count_statuses(manifest)

    log_info(
        f"{report_dir.name}: PASS={counts['PASS']} FAIL={counts['FAIL']} "
        f"INCOMPAT={counts['INCOMPAT']} BLOCKED={counts['BLOCKED']} "
        f"SKIP={counts['SKIP']} readiness={readiness}%"
    )

    updated_manifest = update_manifest(manifest, readiness)

    if dry_run:
        log_info(f"Dry run: would update manifest {manifest_path}")
    else:
        manifest_path.write_text(
            json.dumps(updated_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        log_success(f"Updated manifest readiness: {manifest_path}")

    for filename in MARKDOWN_FILES:
        update_markdown(report_dir / filename, readiness, dry_run)

    log_success(f"{report_dir.name} synchronized -> {readiness}%")
    return True


def main() -> int:
    """Main entry point."""
    args = parse_args()
    reports_dir = Path(args.reports_dir).expanduser().resolve()

    log_info("Starting readiness synchronization")
    log_info(f"Reports directory: {reports_dir}")

    if not reports_dir.exists():
        log_error(f"Reports directory does not exist: {reports_dir}")
        return 1

    if args.release:
        report_dirs = [reports_dir / args.release]
    else:
        report_dirs = sorted(path for path in reports_dir.iterdir() if path.is_dir())

    processed = 0
    for report_dir in report_dirs:
        if process_report(report_dir, dry_run=args.dry_run, verbose=args.verbose):
            processed += 1

    log_success(
        f"Readiness synchronization complete. Processed {processed} report directories."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log_error("Interrupted by user")
        raise SystemExit(1)
