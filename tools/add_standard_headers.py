#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Automatically add repository-standard headers to Python files.

Validation:
    python -m py_compile tools/add_standard_headers.py
    python tools/add_standard_headers.py --dry-run
    python tools/add_standard_headers.py
    python -m pytest tests/test_script_headers.py -v

==============================================================================
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "scripts",
]

REQUIRED_MARKERS = [
    "Author:",
    "Purpose:",
    "Validation:",
]


def build_header(path: Path) -> str:
    return f'''"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    TODO: Describe purpose of {path.name}

Validation:
    python -m py_compile {path.as_posix()}
    python {path.as_posix()} --help

==============================================================================
"""

'''


def process_file(path: Path, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")

    if all(marker in text for marker in REQUIRED_MARKERS):
        return False

    new_text = build_header(path) + text

    if dry_run:
        print(f"[DRY RUN] Would update: {path}")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"[UPDATED] {path}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would be updated",
    )

    args = parser.parse_args()

    updated = 0

    for directory in TARGET_DIRS:
        for path in sorted(directory.rglob("*.py")):
            if process_file(path, args.dry_run):
                updated += 1

    print()
    print(f"Files updated: {updated}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
