#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : scripts/fix_repository_headers.py

Purpose
-------
Add the required repository header markers (Author, Purpose, Validation) to
the maintained Python files that are missing them. tests/test_script_headers.py
enforces these markers, so this script is the repair tool for when that test
fails after a new file is added to TARGETS.

The header is inserted AFTER a shebang line when one exists. Putting a
docstring above ``#!`` silently turns the shebang into an ordinary comment and
the file stops being directly executable.

Safety
------
* ``--check`` reports missing headers and changes nothing (exit 1 if any are
  missing, which suits CI).
* ``--dry-run`` shows what would be written and exits 0.
* Before any real write the original is copied to ``<file>.backup.<timestamp>``
  (``*.backup.*`` is gitignored), so a bad edit is one ``mv`` away from undone.
* Writes are verified by reading the file back.

Usage
-----
    python scripts/fix_repository_headers.py --check
    python scripts/fix_repository_headers.py --dry-run
    python scripts/fix_repository_headers.py

Exit Codes
----------
0   Nothing needed fixing, files were repaired, or --dry-run finished.
1   --check found missing headers, or a write failed verification.
2   Invalid command-line usage (argparse).
130 User interrupted execution.

Log files
---------
    logs/fix_repository_headers.log

Validation:
    python -m py_compile scripts/fix_repository_headers.py
    python scripts/fix_repository_headers.py --check
    python -m pytest tests/test_fix_repository_headers.py -v
===============================================================================
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Bootstrap path, same pattern as the other scripts in this directory, so the
# shared logger imports whether this is run from the repo root or elsewhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Resolved against the repo root, not the current directory, so the result does
# not depend on where the command was started.
TARGETS = [
    "scripts/benchmark_duckdb_pyarrow.py",
    "scripts/benchmark_pandas_polars.py",
    "scripts/logger.py",
    "scripts/validate_core.py",
    "scripts/validate_extended.py",
    "scripts/validate_py315.py",
    "scripts/validate_stack.py",
    "tools/sync_readiness.py",
]

REQUIRED_MARKERS = ("Author:", "Purpose:", "Validation:")

HEADER_TEMPLATE = '''"""
Author: Dr. Ceasar Jackson Jr.

Purpose:
{purpose}

Validation:
python -m py_compile {filename}
"""

'''

PURPOSES = {
    "benchmark_duckdb_pyarrow": "Benchmark DuckDB and PyArrow performance under Python 3.15.",
    "benchmark_pandas_polars": "Benchmark Pandas and Polars performance under Python 3.15.",
    "logger": "Provide shared logging utilities for repository scripts.",
    "validate_core": "Validate Python runtime, tooling, and environment readiness.",
    "validate_extended": "Validate extended data engineering ecosystem compatibility.",
    "validate_py315": "Run end-to-end Python 3.15 compatibility validation.",
    "validate_stack": "Validate core data engineering package stack.",
    "sync_readiness": "Synchronize readiness reports and validation artifacts.",
}


def make_purpose(path: Path) -> str:
    """Purpose line for a known file, or a generic one for anything new."""
    return PURPOSES.get(path.stem, "Repository-maintained Python utility.")


def missing_markers(text: str) -> list[str]:
    return [marker for marker in REQUIRED_MARKERS if marker not in text]


def insert_header(text: str, header: str) -> str:
    """Put the header after a shebang if there is one, else at the top."""
    if text.startswith("#!"):
        first_line, _, rest = text.partition("\n")
        return f"{first_line}\n{header}{rest}"
    return header + text


def process(path: Path, *, check_only: bool, dry_run: bool) -> bool:
    """Handle one file. Returns True when the file lacked a required header."""
    text = path.read_text(encoding="utf-8")
    missing = missing_markers(text)
    if not missing:
        return False

    if check_only:
        log.warning("[MISSING] %s lacks %s", path, ", ".join(missing))
        return True

    new_text = insert_header(
        text, HEADER_TEMPLATE.format(purpose=make_purpose(path), filename=path.name)
    )
    if dry_run:
        log.info("[DRY-RUN] would add a header to %s", path)
        return True

    # Back up first: a header injector rewrites source files wholesale.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.backup.{stamp}")
    shutil.copy2(path, backup)
    path.write_text(new_text, encoding="utf-8")

    # Verify by reading back; restore the original if the write did not take.
    if path.read_text(encoding="utf-8") != new_text:
        shutil.copy2(backup, path)
        raise RuntimeError(f"Write verification failed; restored {path}")
    log.info("[PASS] Updated %s (backup: %s)", path, backup.name)
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add required Author/Purpose/Validation header markers."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report missing headers and change nothing; exit 1 if any are missing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be changed; write nothing and exit 0.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    changed = False

    for item in TARGETS:
        path = PROJECT_ROOT / item
        if not path.exists():
            log.warning("[WARN] Target not found, skipped: %s", item)
            continue
        try:
            changed |= process(path, check_only=args.check, dry_run=args.dry_run)
        except (OSError, ValueError, RuntimeError) as exc:
            # ValueError covers UnicodeDecodeError: a non-UTF-8 file is reported
            # as a failure with exit 1 instead of a traceback.
            log.error("[FAIL] %s: %s", item, exc)
            return 1

    if args.check:
        return 1 if changed else 0
    if not changed:
        log.info("[PASS] All target headers already present; nothing to do.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        # 130 = 128 + SIGINT, the shell convention for "stopped by Ctrl-C".
        sys.stderr.write("\nInterrupted by user.\n")
        raise SystemExit(130) from None
