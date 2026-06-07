#!/usr/bin/env python3
"""
===============================================================================
Python 3.15 Data Engineering Validation Suite
===============================================================================
Script:
    validate_py315.py

Author:
    Dr. Ceasar Jackson Jr.

Project:
    Python 3.15 Data Engineering Validation Suite

Purpose:
    Validate the Python 3.15 sandbox, virtual environment, package manager,
    and core development tooling used by the project.

Usage:
    python scripts/validate_py315.py

Validation:
    python -m py_compile scripts/validate_py315.py
    python -m ruff check scripts/validate_py315.py
    python -m black --check scripts/validate_py315.py
    python scripts/validate_py315.py

Exit Codes:
    0 = Success
    1 = Validation failure
    130 = User interrupted

Logging:
    - Console-based validation output
    - Environment verification details
    - Tooling and package inventory reporting

Operational Notes:
    - Must be executed from the project virtual environment.
    - Validates Python 3.15 runtime requirements.
    - Uses uv-managed package workflows when available.

===============================================================================
"""

from __future__ import annotations

import importlib.util
import pathlib
import platform
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED_VENV = REPO_ROOT / ".venv"


def print_section(title: str) -> None:
    """Print a readable section header."""
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")


def run_command(command: list[str], *, required: bool = False) -> None:
    """Run a command and report success/failure without crashing unless required."""
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, text=True, capture_output=True, check=False)

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

    if result.returncode == 0:
        print("✅ command OK")
    else:
        print(f"⚠️ command exited with status {result.returncode}")
        if required:
            raise SystemExit(result.returncode)


def assert_python315() -> None:
    """Fail fast if this script is not running under Python 3.15."""
    if sys.version_info[:2] != (3, 15):
        raise SystemExit(
            f"❌ Expected Python 3.15, but got {sys.version.split()[0]}\n"
            f"Executable: {sys.executable}"
        )
    print("✅ Python major/minor version is 3.15")


def assert_project_venv() -> None:
    """Validate that Python is running from this project's virtual environment.

    uv-created virtual environments may symlink `.venv/bin/python` to a shared
    interpreter under `~/.local/share/uv/python`. Because of that, resolving
    `sys.executable` can make a valid venv look invalid. The reliable venv
    signal is `sys.prefix`, while `sys.base_prefix` points to the base Python.
    """
    executable_text = str(pathlib.Path(sys.executable))
    expected_prefix = str(EXPECTED_VENV)
    active_prefix = str(pathlib.Path(sys.prefix))
    base_prefix = str(pathlib.Path(sys.base_prefix))

    print("sys.prefix:", active_prefix)
    print("sys.base_prefix:", base_prefix)

    print("Expected prefix:", expected_prefix)
    print("Active prefix:", active_prefix)

    if active_prefix != expected_prefix:
        raise SystemExit(
            "❌ Active Python prefix is not this project's .venv\n"
            f"Expected prefix: {expected_prefix}\n"
            f"Active prefix:   {active_prefix}\n"
            f"Executable:      {executable_text}"
        )

    if sys.prefix == sys.base_prefix:
        raise SystemExit(
            "❌ Python is not running inside a virtual environment\n"
            f"Executable: {executable_text}"
        )

    print("✅ Active Python prefix matches this project's .venv")


def check_import(module_name: str) -> None:
    """Check whether an importable module is available."""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"⚠️ missing module: {module_name}")
        return
    module = __import__(module_name)
    version = getattr(module, "__version__", "version not exposed")
    print(f"✅ {module_name}: {version}")


def main() -> None:
    print_section("Interpreter")
    print("__file__:", pathlib.Path(__file__).resolve())
    print("Computed REPO_ROOT:", REPO_ROOT)
    print("Computed EXPECTED_VENV:", EXPECTED_VENV)
    print("Executable:", sys.executable)
    print("Version:", sys.version)
    print("Platform:", platform.platform())
    print("CWD:", pathlib.Path.cwd())
    print("Project:", REPO_ROOT)

    assert_python315()
    assert_project_venv()

    print_section("Package imports")
    for module_name in ["packaging", "pytest", "ruff", "requests", "rich", "wheel"]:
        check_import(module_name)

    print_section("uv package manager")
    uv_path = shutil.which("uv")
    if uv_path:
        print(f"uv executable: {uv_path}")
        run_command(["uv", "pip", "check"])
        run_command(["uv", "pip", "list"])
    else:
        print("⚠️ uv is not on PATH")

    print_section("pip note")
    if importlib.util.find_spec("pip") is None:
        print("ℹ️ pip is not installed in this uv-managed virtual environment.")
        print("ℹ️ Use `uv pip install ...`, `uv pip list`, and `uv pip check` instead.")
    else:
        run_command([sys.executable, "-m", "pip", "--version"])

    print_section("Result")
    print("✅ Python 3.15 sandbox validation completed successfully")


if __name__ == "__main__":
    main()
