"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Enforce repository-wide script header standards.

Validation:
    python -m py_compile tests/test_script_headers.py
    python -m pytest tests/test_script_headers.py -v

==============================================================================
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = [
    "Author:",
    "Purpose:",
    "Validation:",
]


EXCLUDED_PATH_PARTS = {
    ".venv",
    ".git",
    "__pycache__",
}

# Only enforce header standards on actively maintained repository code.
# Compatibility and benchmark suites are intentionally excluded.

HEADER_ENFORCED_DIRS = [
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "scripts",
]

PYTHON_FILES = [
    path
    for root in HEADER_ENFORCED_DIRS
    for path in root.rglob("*.py")
    if not any(part in EXCLUDED_PATH_PARTS for part in path.parts)
]


def read_text(path: Path) -> str:
    """Read UTF-8 text from a file."""
    return path.read_text(encoding="utf-8")


def test_python_files_discovered() -> None:
    """Ensure repository contains Python files to validate."""
    assert PYTHON_FILES, "No Python files discovered in repository"


def test_python_files_contain_required_headers() -> None:
    """Verify required header markers exist in maintained repository files."""
    failures: list[str] = []

    for path in PYTHON_FILES:
        text = read_text(path)
        missing = [marker for marker in REQUIRED_MARKERS if marker not in text]

        if missing:
            failures.append(f"{path}: missing {missing}")

    assert not failures, "\n".join(failures)
