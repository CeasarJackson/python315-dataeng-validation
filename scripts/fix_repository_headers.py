#!/usr/bin/env python3
"""
Author: Dr. Ceasar Jackson Jr.

Purpose:
Automatically add required repository header markers
(Author, Purpose, Validation) to maintained Python files.

Validation:
python scripts/fix_repository_headers.py --check
python scripts/fix_repository_headers.py
python -m pytest -q
"""

from pathlib import Path
import argparse

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

HEADER_TEMPLATE = '''"""
Author: Dr. Ceasar Jackson Jr.

Purpose:
{purpose}

Validation:
python -m py_compile {filename}
"""

'''


def make_purpose(path: Path) -> str:
    stem = path.stem

    mapping = {
        "benchmark_duckdb_pyarrow": "Benchmark DuckDB and PyArrow performance under Python 3.15.",
        "benchmark_pandas_polars": "Benchmark Pandas and Polars performance under Python 3.15.",
        "logger": "Provide shared logging utilities for repository scripts.",
        "validate_core": "Validate Python runtime, tooling, and environment readiness.",
        "validate_extended": "Validate extended data engineering ecosystem compatibility.",
        "validate_py315": "Run end-to-end Python 3.15 compatibility validation.",
        "validate_stack": "Validate core data engineering package stack.",
        "sync_readiness": "Synchronize readiness reports and validation artifacts.",
    }

    return mapping.get(stem, "Repository-maintained Python utility.")


def process(path: Path, check_only: bool) -> bool:
    text = path.read_text()

    required = ("Author:", "Purpose:", "Validation:")

    if all(x in text for x in required):
        return False

    header = HEADER_TEMPLATE.format(
        purpose=make_purpose(path),
        filename=path.name,
    )

    if check_only:
        print(f"MISSING HEADER: {path}")
        return True

    path.write_text(header + text)
    print(f"UPDATED: {path}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changed = False

    for item in TARGETS:
        path = Path(item)

        if path.exists():
            changed |= process(path, args.check)

    if args.check:
        raise SystemExit(1 if changed else 0)


if __name__ == "__main__":
    main()
