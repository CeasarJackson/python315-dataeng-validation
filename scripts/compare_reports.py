#!/usr/bin/env python3
"""
scripts/compare_reports.py
===========================
Diffs two report cycles and shows what changed between them.

Usage:
    python scripts/compare_reports.py 3.15.0b1 3.15.0b2
    python scripts/compare_reports.py 3.15.0b2 3.15.0rc1 --format markdown
"""

import argparse
import json
from pathlib import Path

REPO = Path(__file__).parent.parent
REPORTS = REPO / "reports"

STATUS_RANK = {"PASS": 0, "INCOMPAT": 1, "SKIP": 2, "FAIL": 3}
STATUS_BADGE = {
    "PASS": "✅ PASS",
    "FAIL": "❌ FAIL",
    "INCOMPAT": "⚠️  INCOMPAT",
    "SKIP": "⏭️  SKIP",
    "PENDING": "🔲 PENDING",
}


def load_manifest(release):
    path = REPORTS / release / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No manifest found for {release}.\n"
            f"Expected: {path}\n"
            f"Run: python scripts/generate_report.py --release {release}"
        )
    return json.loads(path.read_text())


def compare(old_release, new_release, fmt="terminal"):
    old = load_manifest(old_release)
    new = load_manifest(new_release)

    old_results = old.get("results", {})
    new_results = new.get("results", {})

    all_packages = sorted(set(list(old_results.keys()) + list(new_results.keys())))

    changes = []
    regressions = []
    improvements = []
    unchanged = []
    new_entries = []

    for pkg in all_packages:
        o = old_results.get(pkg)
        n = new_results.get(pkg)

        if o is None:
            new_entries.append((pkg, n))
            continue

        if n is None:
            changes.append((pkg, o["status"], "REMOVED", "dropped from suite"))
            continue

        os_, ns_ = o["status"], n["status"]
        if os_ == ns_:
            unchanged.append(pkg)
        else:
            o_rank = STATUS_RANK.get(os_, 9)
            n_rank = STATUS_RANK.get(ns_, 9)
            if n_rank < o_rank:
                improvements.append(
                    (pkg, os_, ns_, n.get("version", ""), n.get("note", ""))
                )
            else:
                regressions.append(
                    (pkg, os_, ns_, n.get("version", ""), n.get("reason", ""))
                )
            changes.append((pkg, os_, ns_, n.get("reason", n.get("note", ""))))

    if fmt == "markdown":
        _print_markdown(
            old_release,
            new_release,
            old,
            new,
            improvements,
            regressions,
            unchanged,
            new_entries,
        )
    else:
        _print_terminal(
            old_release,
            new_release,
            old,
            new,
            improvements,
            regressions,
            unchanged,
            new_entries,
        )


def _print_terminal(
    old_rel, new_rel, old, new, improvements, regressions, unchanged, new_entries
):
    print(f"\n{'='*60}")
    print(f"Compatibility Delta: {old_rel} → {new_rel}")
    print(f"{'='*60}")
    print(
        f"  Old date : {old.get('test_date','?')}  "
        f"({old.get('packages_pass','?')} PASS / "
        f"{old.get('packages_fail','?')} FAIL / "
        f"{old.get('packages_incompat','?')} INCOMPAT)"
    )
    print(
        f"  New date : {new.get('test_date','?')}  "
        f"({new.get('packages_pass','?')} PASS / "
        f"{new.get('packages_fail','?')} FAIL / "
        f"{new.get('packages_incompat','?')} INCOMPAT)"
    )

    prod_delta = new.get("production_readiness_pct", 0) - old.get(
        "production_readiness_pct", 0
    )
    if prod_delta != 0:
        arrow = "▲" if prod_delta > 0 else "▼"
        print(
            f"  Readiness: {old.get('production_readiness_pct')}% → "
            f"{new.get('production_readiness_pct')}%  ({arrow}{abs(prod_delta)}%)"
        )

    if improvements:
        print(f"\n  ✅ Improvements ({len(improvements)})")
        for pkg, old_s, new_s, ver, note in improvements:
            n = f"  [{note}]" if note else ""
            print(f"     {pkg:<22} {old_s} → {new_s}  {ver}{n}")

    if regressions:
        print(f"\n  ❌ Regressions ({len(regressions)})")
        for pkg, old_s, new_s, ver, note in regressions:
            n = f"  [{note}]" if note else ""
            print(f"     {pkg:<22} {old_s} → {new_s}  {ver}{n}")

    if new_entries:
        print(f"\n  🆕 New packages ({len(new_entries)})")
        for pkg, r in new_entries:
            print(f"     {pkg:<22} {r['status']}  {r.get('version','')}")

    print(f"\n  Unchanged: {len(unchanged)} packages")
    print()


def _print_markdown(
    old_rel, new_rel, old, new, improvements, regressions, unchanged, new_entries
):
    from datetime import date

    lines = [
        f"# Compatibility Delta: {old_rel} \u2192 {new_rel}",
        "",
        f"**Generated:** {date.today().isoformat()}",
        "",
        "## Overview",
        "",
        "| | Previous | Current | Delta |",
        "|-|----------|---------|-------|",
        f"| Release | {old_rel} | {new_rel} | |",
        f"| Test Date | {old.get('test_date','?')} | {new.get('test_date','?')} | |",
        f"| PASS | {old.get('packages_pass','?')} | {new.get('packages_pass','?')} | |",
        f"| FAIL | {old.get('packages_fail','?')} | {new.get('packages_fail','?')} | |",
        f"| INCOMPAT | {old.get('packages_incompat','?')} | {new.get('packages_incompat','?')} | |",
        "",
    ]

    if improvements:
        lines += [
            "## Improvements",
            "",
            "| Package | Previous | Current | Notes |",
            "|---------|----------|---------|-------|",
        ]
        for pkg, os_, ns_, ver, note in improvements:
            lines.append(f"| {pkg} | {os_} | {ns_} | {note} |")
        lines.append("")

    if regressions:
        lines += [
            "## Regressions",
            "",
            "| Package | Previous | Current | Reason |",
            "|---------|----------|---------|--------|",
        ]
        for pkg, os_, ns_, ver, note in regressions:
            lines.append(f"| {pkg} | {os_} | {ns_} | {note} |")
        lines.append("")

    if new_entries:
        lines += [
            "## New Packages",
            "",
            "| Package | Status | Version |",
            "|---------|--------|---------|",
        ]
        for pkg, r in new_entries:
            lines.append(f"| {pkg} | {r['status']} | {r.get('version','')} |")
        lines.append("")

    lines += [f"*{len(unchanged)} packages unchanged.*", ""]
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Compare two compatibility report cycles"
    )
    parser.add_argument("old", help="Previous release, e.g. 3.15.0b1")
    parser.add_argument("new", help="New release, e.g. 3.15.0b2")
    parser.add_argument(
        "--format",
        choices=["terminal", "markdown"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    args = parser.parse_args()

    try:
        compare(args.old, args.new, fmt=args.format)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
