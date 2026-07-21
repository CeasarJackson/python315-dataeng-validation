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

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = [
    "Author:",
    "Purpose:",
    "Validation:",
]

SHEBANG_PREFIX = "#!"


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


# Shell scripts are always expected to be directly executable.
SHELL_SCRIPTS = [
    path
    for path in PROJECT_ROOT.rglob("*.sh")
    if not any(part in EXCLUDED_PATH_PARTS for part in path.parts)
]

# Python modules that are imported rather than invoked directly. These are
# intentionally exempt from the executable-bit convention.
NON_EXECUTABLE_NAMES = {"__init__.py"}


def read_text(path: Path) -> str:
    """Read UTF-8 text from a file."""
    return path.read_text(encoding="utf-8")


def has_shebang(path: Path) -> bool:
    """Return True when a file begins with a shebang line."""
    return read_text(path).startswith(SHEBANG_PREFIX)


def is_executable(path: Path) -> bool:
    """Return True when the owner-execute bit is set."""
    return os.access(path, os.X_OK)


def is_exempt(path: Path) -> bool:
    """Return True for modules exempt from the executable convention."""
    return path.name in NON_EXECUTABLE_NAMES or path.name.startswith("test_")


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


def test_executable_python_files_have_shebang() -> None:
    """An executable bit is meaningless without a shebang to interpret it."""
    failures = [
        f"{path}: executable but has no shebang line"
        for path in PYTHON_FILES
        if is_executable(path) and not has_shebang(path)
    ]

    assert not failures, "\n".join(failures)


def test_shebang_python_files_are_executable() -> None:
    """A shebang implies direct invocation, which requires the execute bit."""
    failures = [
        f"{path}: has a shebang but is not executable"
        for path in PYTHON_FILES
        if has_shebang(path) and not is_executable(path) and not is_exempt(path)
    ]

    assert not failures, "\n".join(failures)


def test_shell_scripts_are_executable() -> None:
    """Verify every shell script can be invoked directly."""
    failures = [
        f"{path}: shell script is not executable"
        for path in SHELL_SCRIPTS
        if not is_executable(path)
    ]

    assert not failures, "\n".join(failures)


def test_shell_scripts_have_shebang() -> None:
    """Verify every shell script declares an interpreter."""
    failures = [
        f"{path}: shell script has no shebang line"
        for path in SHELL_SCRIPTS
        if not has_shebang(path)
    ]

    assert not failures, "\n".join(failures)
