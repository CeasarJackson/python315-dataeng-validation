#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : scripts/build_assessment_pdf.py

Purpose
-------
Render the formal readiness assessment PDF for one release directly from that
release's ``manifest.json``. Earlier assessments were assembled by hand, which
is how a stale June PDF ended up being copied into later report folders: the
tests only check that a PDF *exists*, not that it describes the release it
sits in. This script closes that gap by making the PDF a pure function of the
manifest.

Every number, status, version and reason in the output comes from the
manifest. Nothing is typed in by hand. Before rendering, the script refuses to
continue unless the manifest is internally consistent:

    * ``release`` equals the requested release (a mislabelled report is the
      failure mode that already forced two reports into quarantine),
    * the per-package results agree with the ``packages_*`` counters, and
    * ``production_readiness_pct`` agrees with the project's readiness formula
      recomputed from the results.

If a previous release is supplied, a "changes" table is derived by comparing
the two manifests.

Output is deterministic (ReportLab ``invariant`` mode): rerunning on the same
manifest produces byte-identical output, so a diff of the PDF means the data
changed.

Security
--------
Reads one or two manifest files and writes one PDF. It touches no credentials,
makes no network calls, and logs only release names, counts and file paths.

Usage
-----
    python scripts/build_assessment_pdf.py --release 3.15.0 --dry-run
    python scripts/build_assessment_pdf.py --release 3.15.0 --previous 3.15.0rc2
    python scripts/build_assessment_pdf.py --release 3.15.0 --previous 3.15.0rc2 --force

Requires ReportLab (``uv pip install reportlab``). It is deliberately not part
of the pinned validation requirements, so that installing it never alters the
environment a compatibility baseline was measured in.

Exit Codes
----------
0   PDF written (or dry run succeeded).
1   Validation or operational failure (bad manifest, output exists, no
    ReportLab).
2   Invalid command-line usage.
130 User interrupted execution.

Log files
---------
    logs/build_assessment_pdf.log

Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Generate the per-release readiness assessment PDF from the
        release manifest so the PDF cannot drift from the evidence.
    Validation: python -m py_compile scripts/build_assessment_pdf.py; python scripts/build_assessment_pdf.py --release 3.15.0 --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

# Same bootstrap pattern as the other scripts: run from anywhere, and import
# cleanly from the pytest suite.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"
PDF_NAME = "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"

REQUIRED_KEYS = (
    "project",
    "release",
    "release_type",
    "test_date",
    "platform",
    "python_build",
    "python_runtime",
    "tester",
    "suite_version",
    "docker_image",
    "packages_tested",
    "packages_pass",
    "packages_fail",
    "packages_incompat",
    "packages_blocked",
    "packages_skip",
    "environment_consistent",
    "constraint_violations",
    "production_readiness_pct",
    "results",
)

# Readiness weighting. This mirrors scripts/generate_report.py and
# tools/sync_readiness.py (SKIP excluded from the denominator). It is repeated
# here, not imported, so this script stays usable on a machine that only has
# the manifest; check_readiness() fails loudly if the copies ever diverge.
WEIGHTS = {"PASS": 1.0, "BLOCKED": 0.50, "INCOMPAT": 0.25, "FAIL": 0.0}

# Lower rank = healthier. SKIP is deliberately absent: moving into or out of
# SKIP is a change in *coverage*, not a change in compatibility, and the
# runbook requires the two to be reported separately.
HEALTH_RANK = {"PASS": 0, "INCOMPAT": 1, "BLOCKED": 2, "FAIL": 3}

RELEASE_LABELS = {
    "ga": "General Availability",
    "rc": "Release Candidate",
    "beta": "Beta",
}


class ManifestError(Exception):
    """Raised when a manifest is missing, malformed or self-contradictory."""


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------
def load_manifest(release: str) -> tuple[dict[str, Any], str]:
    """Load reports/<release>/manifest.json and return (data, sha256)."""
    path = REPORTS / release / "manifest.json"
    if not path.is_file():
        raise ManifestError(f"Manifest not found: {path}")

    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(
            f"Manifest is not valid UTF-8 JSON: {path} ({exc})"
        ) from exc

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ManifestError(f"{path}: missing required keys {missing}")

    # A report whose directory name and contents disagree is exactly the
    # mislabelling that already poisoned the rc1 evidence; refuse to render it.
    if data["release"] != release:
        raise ManifestError(
            f"{path}: manifest says release={data['release']!r} but the "
            f"directory is {release!r}"
        )
    return data, hashlib.sha256(raw).hexdigest()


def compute_readiness(counts: Counter[str], total: int) -> float:
    """Apply the project readiness formula to a status tally."""
    denominator = total - counts.get("SKIP", 0)
    if denominator <= 0:
        return 0.0
    score = sum(counts.get(status, 0) * weight for status, weight in WEIGHTS.items())
    return 100.0 * score / denominator


def check_consistency(manifest: dict[str, Any]) -> None:
    """Fail unless counters, results and readiness all agree."""
    results: dict[str, dict[str, Any]] = manifest["results"]
    counts: Counter[str] = Counter(entry["status"] for entry in results.values())

    expected = {
        "packages_pass": counts.get("PASS", 0),
        "packages_fail": counts.get("FAIL", 0),
        "packages_incompat": counts.get("INCOMPAT", 0),
        "packages_blocked": counts.get("BLOCKED", 0),
        "packages_skip": counts.get("SKIP", 0),
        "packages_tested": len(results),
    }
    mismatches = [
        f"{key}: manifest={manifest[key]} results={value}"
        for key, value in expected.items()
        if manifest[key] != value
    ]
    if mismatches:
        raise ManifestError("Counters disagree with results: " + "; ".join(mismatches))

    recomputed = compute_readiness(counts, len(results))
    stated = manifest["production_readiness_pct"]
    # Allow one point for rounding-mode differences between the two tools; a
    # larger gap means the formula or the data has changed underneath us.
    if abs(recomputed - stated) > 1.0:
        raise ManifestError(
            f"production_readiness_pct={stated} but the formula gives "
            f"{recomputed:.1f} from the results"
        )
    log.info(
        "[PASS] manifest consistent: %s results, readiness %s%% (formula %.1f%%)",
        len(results),
        stated,
        recomputed,
    )


# ---------------------------------------------------------------------------
# Derived content
# ---------------------------------------------------------------------------
def classify_changes(
    current: dict[str, Any], previous: dict[str, Any]
) -> tuple[list[tuple[str, str, str, str, str]], int]:
    """Compare two manifests.

    Returns (rows, unchanged_count); each row is
    (kind, package, previous_status, current_status, current_version).
    """
    cur: dict[str, dict[str, Any]] = current["results"]
    prev: dict[str, dict[str, Any]] = previous["results"]
    rows: list[tuple[str, str, str, str, str]] = []
    unchanged = 0

    for name in sorted(set(cur) | set(prev)):
        old = prev.get(name, {}).get("status", "(absent)")
        new = cur.get(name, {}).get("status", "(absent)")
        version = str(cur.get(name, {}).get("version", "-"))
        if old == new:
            unchanged += 1
            continue
        if "SKIP" in (old, new) or "(absent)" in (old, new):
            kind = "Coverage change"
        elif HEALTH_RANK[new] < HEALTH_RANK[old]:
            kind = "Improvement"
        else:
            kind = "Regression"
        rows.append((kind, name, old, new, version))

    order = {"Regression": 0, "Improvement": 1, "Coverage change": 2}
    rows.sort(key=lambda row: (order[row[0]], row[1]))
    return rows, unchanged


def docker_sourced(manifest: dict[str, Any]) -> list[str]:
    """Names of results whose note says they ran inside a Docker image."""
    return [
        name
        for name, entry in manifest["results"].items()
        if "docker" in str(entry.get("note", "")).lower()
    ]


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------
def build_pdf(
    manifest: dict[str, Any],
    digest: str,
    previous: dict[str, Any] | None,
    out_path: Path,
) -> None:
    """Render the assessment to *out_path* (atomically)."""
    # Imported here so --help / py_compile work without ReportLab installed.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    results: dict[str, dict[str, Any]] = manifest["results"]
    counts: Counter[str] = Counter(e["status"] for e in results.values())
    release = manifest["release"]
    label = RELEASE_LABELS.get(
        manifest["release_type"], str(manifest["release_type"]).upper()
    )
    pct = manifest["production_readiness_pct"]

    base = getSampleStyleSheet()
    ink = colors.HexColor("#1b2430")
    muted = colors.HexColor("#5b6675")
    accent = colors.HexColor("#1f4e79")
    rule = colors.HexColor("#c9d1da")

    title = ParagraphStyle(
        "T",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=ink,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "S",
        parent=base["Normal"],
        fontSize=11,
        leading=14,
        textColor=muted,
        spaceAfter=14,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=accent,
        spaceBefore=14,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "B", parent=base["BodyText"], fontSize=10, leading=14, textColor=ink
    )
    bullet = ParagraphStyle(
        "BL", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=3
    )
    cell = ParagraphStyle("C", parent=body, fontSize=8.8, leading=11.5)
    cell_b = ParagraphStyle("CB", parent=cell, fontName="Helvetica-Bold")
    head = ParagraphStyle(
        "CH", parent=cell, fontName="Helvetica-Bold", textColor=colors.white
    )
    big = ParagraphStyle(
        "BIG",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=34,
        textColor=accent,
    )

    tint = {
        "PASS": colors.HexColor("#d9f2e3"),
        "INCOMPAT": colors.HexColor("#fdecc8"),
        "BLOCKED": colors.HexColor("#f9d6d5"),
        "SKIP": colors.HexColor("#e4e6ea"),
        "FAIL": colors.HexColor("#f4b6b3"),
    }

    def para(text: Any, style: ParagraphStyle = body) -> Paragraph:
        # Reasons contain backticks, <, > and & (e.g. "<3.15"); escape them
        # so ReportLab's mini-markup parser does not choke or eat them.
        return Paragraph(escape(str(text)), style)

    def table(rows: list[list[Any]], widths: list[float], header: bool = True) -> Table:
        t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
        style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, rule),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), accent)]
        t.setStyle(TableStyle(style))
        return t

    width = letter[0] - 1.6 * inch
    story: list[Any] = []

    # ---- Title block ------------------------------------------------------
    story.append(
        Paragraph("Python 3.15 Data Engineering<br/>Readiness Assessment", title)
    )
    story.append(
        Paragraph(
            escape(
                f"{label} - Python {manifest['python_runtime']} - tested {manifest['test_date']}"
            ),
            subtitle,
        )
    )

    story.append(Paragraph(f"{pct}%", big))
    story.append(
        Paragraph(
            escape(
                f"overall readiness  |  {counts.get('PASS', 0)} PASS  -  "
                f"{counts.get('INCOMPAT', 0)} INCOMPAT  -  {counts.get('BLOCKED', 0)} BLOCKED  -  "
                f"{counts.get('SKIP', 0)} SKIP  -  {counts.get('FAIL', 0)} FAIL  "
                f"(of {len(results)} packages)"
            ),
            ParagraphStyle("K", parent=body, textColor=muted, spaceAfter=10),
        )
    )

    # ---- Executive summary ------------------------------------------------
    story.append(Paragraph("Executive summary", h2))
    non_pass = [(n, e) for n, e in results.items() if e["status"] != "PASS"]
    summary = (
        (
            f"Python {manifest['python_runtime']} was validated on {manifest['platform']} using "
            f"{manifest['package_manager']}. Of {len(results)} packages probed, "
            f"{counts.get('PASS', 0)} passed and none failed outright. "
            f"{len(non_pass)} did not pass: "
            + "; ".join(f"{n} ({e['status']})" for n, e in non_pass)
            + "."
        )
        if non_pass
        else (
            f"Python {manifest['python_runtime']} was validated on {manifest['platform']}. "
            f"All {len(results)} packages passed."
        )
    )
    story.append(para(summary))

    if previous is not None:
        story.append(Spacer(1, 5))
        story.append(
            para(
                f"Compared with {previous['release']} ({previous['test_date']}), overall readiness "
                f"moved from {previous['production_readiness_pct']}% to {pct}%."
            )
        )

    # ---- At a glance ------------------------------------------------------
    story.append(Paragraph("Test environment", h2))
    glance = [
        ("Release", f"{release} ({label})"),
        ("Python runtime", manifest["python_runtime"]),
        ("Python build", manifest["python_build"]),
        ("Platform", manifest["platform"]),
        ("Test date", manifest["test_date"]),
        ("Tester", manifest["tester"]),
        ("Suite version", manifest["suite_version"]),
        ("Docker image", manifest["docker_image"]),
        (
            "Environment consistent",
            "yes" if manifest["environment_consistent"] else "NO - see limitations",
        ),
    ]
    story.append(
        table(
            [[para(k, cell_b), para(v, cell)] for k, v in glance],
            [1.7 * inch, width - 1.7 * inch],
            header=False,
        )
    )

    # ---- Results ----------------------------------------------------------
    story.append(Paragraph("Package results", h2))
    rows: list[list[Any]] = [
        [
            para("Package", head),
            para("Status", head),
            para("Version", head),
            para("Notes", head),
        ]
    ]
    status_cells: list[tuple[int, str]] = []
    for index, (name, entry) in enumerate(results.items(), start=1):
        notes = entry.get("reason") or entry.get("note") or ""
        rows.append(
            [
                para(name, cell_b),
                para(entry["status"], cell_b),
                para(entry.get("version", "-"), cell),
                para(notes, cell),
            ]
        )
        status_cells.append((index, entry["status"]))
    res_table = table(rows, [1.25 * inch, 0.8 * inch, 1.0 * inch, width - 3.05 * inch])
    res_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (1, i), (1, i), tint.get(s, colors.white))
                for i, s in status_cells
            ]
        )
    )
    story.append(res_table)

    # ---- Changes vs previous ----------------------------------------------
    if previous is not None:
        change_rows, unchanged = classify_changes(manifest, previous)
        story.append(Paragraph(f"Changes since {previous['release']}", h2))
        if change_rows:
            data: list[list[Any]] = [
                [para(h, head) for h in ("Change", "Package", "Was", "Now", "Version")]
            ]
            for kind, name, old, new, version in change_rows:
                data.append(
                    [
                        para(kind, cell_b),
                        para(name, cell),
                        para(old, cell),
                        para(new, cell_b),
                        para(version, cell),
                    ]
                )
            story.append(
                table(
                    data,
                    [
                        1.3 * inch,
                        1.5 * inch,
                        1.0 * inch,
                        1.0 * inch,
                        width - 4.8 * inch,
                    ],
                )
            )
        story.append(Spacer(1, 4))
        story.append(para(f"{unchanged} package(s) unchanged."))
        story.append(Spacer(1, 3))
        story.append(
            para(
                "Coverage changes (moving into or out of SKIP) are reported separately from "
                "compatibility changes: a package that was not measured before is not evidence "
                "of a regression or an improvement in Python itself."
            )
        )

    # ---- Limitations -------------------------------------------------------
    limits: list[str] = []
    if not manifest["environment_consistent"]:
        for violation in manifest["constraint_violations"]:
            limits.append(f"Environment constraint violation: {violation}")
        limits.append(
            "A package that declares no support for this Python can still import and run; the "
            "suite classifies it INCOMPAT on declared support, not on smoke-test outcome."
        )
    tag = str(manifest["docker_image"]).split(":")[-1]
    docker_names = docker_sourced(manifest)
    for name in docker_names:
        limits.append(
            f"{name} was exercised inside the Docker image tagged '{tag}', not on the "
            f"{manifest['python_runtime']} runtime. It shows the package works in that "
            "container; it is not Python 3.15 evidence."
        )
    if docker_names:
        # Be explicit about how much of the headline number rests on those
        # results: recompute with them treated as not measured (SKIP).
        adjusted: Counter[str] = Counter(
            "SKIP" if name in docker_names else entry["status"]
            for name, entry in results.items()
        )
        limits.append(
            f"The headline {pct}% counts those Docker-sourced results as PASS. Treating them as "
            f"not measured (SKIP) instead, readiness would be "
            f"{round(compute_readiness(adjusted, len(results)))}%."
        )
    for name, entry in results.items():
        if entry["status"] == "SKIP":
            limits.append(
                f"{name} was not measured ({entry.get('reason') or entry.get('version')}); "
                "it is excluded from the readiness score."
            )
        elif entry["status"] == "BLOCKED":
            limits.append(
                f"{name} is BLOCKED: {entry.get('reason', 'no reason recorded')}."
            )

    if limits:
        story.append(Paragraph("Evidence and limitations", h2))
        for item in limits:
            story.append(Paragraph(escape(item), bullet, bulletText="-"))

    # ---- Method ------------------------------------------------------------
    story.append(
        KeepTogether(
            [
                Paragraph("How readiness is calculated", h2),
                para(
                    "Readiness = (PASS + 0.50 x BLOCKED + 0.25 x INCOMPAT) / (packages - SKIP), "
                    "rounded to a whole percent. SKIP is excluded because an unmeasured package is "
                    "neither compatible nor incompatible. The weights are this project's convention, "
                    "not an industry standard, and the score summarises this suite's probes only; it "
                    "is not a certification of any package or deployment."
                ),
            ]
        )
    )

    def footer(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(
            0.8 * inch,
            0.5 * inch,
            f"{manifest['project']} - {release} - manifest sha256 {digest[:12]}",
        )
        canvas.drawRightString(letter[0] - 0.8 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".pdf.tmp")
    doc = SimpleDocTemplate(
        str(tmp_path),
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title=f"Python {manifest['python_runtime']} Data Engineering Readiness Assessment",
        author=manifest["tester"],
        subject=f"Readiness assessment for Python {release}",
        keywords="Python 3.15, data engineering, compatibility, readiness",
        invariant=1,  # fixed timestamps/IDs -> byte-identical reruns
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    # Atomic replace: a crash mid-build never leaves a half-written PDF where
    # the tests expect a finished one.
    os.replace(tmp_path, out_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the readiness assessment PDF from a release manifest."
    )
    parser.add_argument(
        "--release", required=True, help="Release directory name, e.g. 3.15.0"
    )
    parser.add_argument(
        "--previous", help="Earlier release to diff against, e.g. 3.15.0rc2"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=f"Output path (default: reports/<release>/{PDF_NAME})",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing PDF"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate only; write nothing"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_path: Path = args.output or (REPORTS / args.release / PDF_NAME)

    try:
        manifest, digest = load_manifest(args.release)
        check_consistency(manifest)
        previous = load_manifest(args.previous)[0] if args.previous else None
        if previous is not None:
            check_consistency(previous)
    except ManifestError as exc:
        log.error("[FAIL] %s", exc)
        return 1

    if out_path.exists() and not args.force and not args.dry_run:
        log.error("[FAIL] %s already exists; pass --force to replace it", out_path)
        return 1

    if args.dry_run:
        log.info("[DRY ] would write %s (manifest sha256 %s)", out_path, digest[:12])
        return 0

    try:
        import reportlab  # noqa: F401
    except ImportError:
        log.error(
            "[FAIL] ReportLab is not installed. Install it with: uv pip install reportlab"
        )
        return 1

    build_pdf(manifest, digest, previous, out_path)
    head = out_path.read_bytes()[:5]
    if head != b"%PDF-" or out_path.stat().st_size == 0:
        log.error("[FAIL] output is not a valid PDF: %s", out_path)
        return 1
    log.info(
        "[PASS] wrote %s (%s bytes, manifest sha256 %s)",
        out_path,
        f"{out_path.stat().st_size:,}",
        digest[:12],
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
