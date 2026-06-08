"""
============================================================================
Author: Dr. Ceasar Jackson Jr.
Project: Python 3.15 Data Engineering Validation Suite
File: test_repository_standards.py
Purpose:
    Enforce repository-wide coding and documentation standards.

Validation:
    python -m py_compile tests/test_repository_standards.py
    python -m pytest tests/test_repository_standards.py -v

Standards Enforced:
    - Author header present
    - Purpose section present
    - Validation section present
    - No empty Python files
    - Test modules contain at least one test
============================================================================
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PYTHON_FILES = [
    path
    for path in PROJECT_ROOT.rglob("*.py")
    if ".venv" not in str(path) and "__pycache__" not in str(path)
]


REQUIRED_HEADER_MARKERS = [
    "Author:",
    "Purpose:",
    "Validation:",
]


# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


# ----------------------------------------------------------------------------
# Repository Standards Tests
# ----------------------------------------------------------------------------


def test_python_files_exist() -> None:
    """Verify repository contains Python files."""
    assert PYTHON_FILES


def test_no_empty_python_files() -> None:
    """Verify Python source files are not empty."""
    for path in PYTHON_FILES:
        assert read_text(path).strip(), f"Empty file: {path}"


def test_test_modules_contain_tests() -> None:
    """Verify test modules contain at least one test function."""
    for path in PROJECT_ROOT.glob("tests/test_*.py"):
        text = read_text(path)
        assert "def test_" in text, f"No tests found in {path}"


def test_repository_test_files_have_standard_sections() -> None:
    """Verify repository test files contain required documentation sections."""
    for path in PROJECT_ROOT.glob("tests/test_*.py"):
        text = read_text(path)

        missing = [marker for marker in REQUIRED_HEADER_MARKERS if marker not in text]

        assert not missing, f"{path} missing required markers: {missing}"
