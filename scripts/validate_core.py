"""
===============================================================================
===============================================================================
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : scripts/validate_core.py

Purpose
-------
Run Python 3.15 validation checks for the project runtime and data-engineering stack.

Usage
-----
python scripts/validate_core.py

Validation
----------
python -m py_compile scripts/validate_core.py
python -m ruff check scripts/validate_core.py
python -m black --check scripts/validate_core.py
python scripts/validate_core.py

Exit Codes
----------
0   Success.
1   Failure or validation error.
130 User interrupted execution.

Operational Notes
-----------------
- Keep this script compatible with the active Python 3.15 validation environment.
- Prefer deterministic inputs and explicit validation commands.
- Preserve readable output suitable for terminal review and release notes.
- Keep this header intact for portfolio, audit, and future-maintainer reference.

===============================================================================


Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Run core Python 3.15 runtime and data-engineering validation checks.
    Validation: python -m py_compile scripts/validate_core.py; python scripts/validate_core.py
"""

from __future__ import annotations

import importlib
import os
import platform
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure scripts/ is on the path so logger.py resolves correctly
# when this file is run directly (not as part of a package).
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 15

# Development tools that must be importable in the active environment.
# Each entry is (import_name, display_name).
DEV_TOOLS: list[tuple[str, str]] = [
    ("pytest", "pytest"),
    ("ruff", "ruff"),
    ("black", "black"),
    ("mypy", "mypy"),
    ("rich", "rich"),
    ("requests", "requests"),
    ("packaging", "packaging"),
    ("wheel", "wheel"),
    ("colorlog", "colorlog"),  # Required for this suite's logging
]


# ---------------------------------------------------------------------------
# Individual check functions — each returns True on pass, False on fail.
# ---------------------------------------------------------------------------


def check_python_version() -> bool:
    """Assert Python >= 3.15.

    Python 3.15 introduces several internal ABI changes relevant to C-extension
    packages.  Any lower version invalidates the rest of the validation suite.
    """
    major, minor, micro = sys.version_info[:3]
    release_level = sys.version_info.releaselevel  # 'alpha', 'beta', 'final'

    log.debug("Raw version info: %s", sys.version)

    if major == REQUIRED_PYTHON_MAJOR and minor >= REQUIRED_PYTHON_MINOR:
        log.info(
            "[PASS] Python %d.%d.%d (%s) — meets >= 3.15 requirement",
            major,
            minor,
            micro,
            release_level,
        )
        if release_level != "final":
            log.warning(
                "[NOTE] This is a %s build — expect rough edges in "
                "C-extension packages.",
                release_level,
            )
        return True
    else:
        log.error(
            "[FAIL] Python %d.%d.%d detected — require >= 3.15.  "
            "Activate the correct virtual environment.",
            major,
            minor,
            micro,
        )
        return False


def check_platform() -> bool:
    """Confirm macOS ARM64 (darwin / arm64).

    The validation suite is authored and tested on Apple Silicon.  On other
    platforms some package builds (e.g. PyArrow source builds) may behave
    differently; this check logs a WARNING rather than failing outright.
    """
    system = platform.system().lower()  # 'darwin', 'linux', 'windows'
    machine = platform.machine().lower()  # 'arm64', 'x86_64', 'amd64'

    log.debug("platform.system()=%s  platform.machine()=%s", system, machine)

    if system == "darwin" and machine == "arm64":
        log.info("[PASS] Platform: macOS ARM64 (Apple Silicon) — validated target")
        return True
    else:
        log.warning(
            "[WARN] Platform: %s / %s — not the primary validated target "
            "(macOS ARM64).  Results may differ.",
            platform.system(),
            platform.machine(),
        )
        # Return True — wrong platform is a warning, not a blocker
        return True


def check_virtual_environment() -> bool:
    """Confirm a virtual environment is active.

    Checks both VIRTUAL_ENV (set by venv/uv activate) and the presence of a
    pyvenv.cfg next to the Python executable, which covers edge cases where
    VIRTUAL_ENV is unset but a venv is still in use.
    """
    venv_env = os.environ.get("VIRTUAL_ENV", "")
    pyvenv_cfg = Path(sys.executable).parent.parent / "pyvenv.cfg"

    log.debug("VIRTUAL_ENV=%r  pyvenv.cfg_exists=%s", venv_env, pyvenv_cfg.exists())

    if venv_env:
        log.info("[PASS] Virtual environment active: %s", venv_env)
        return True
    elif pyvenv_cfg.exists():
        log.info("[PASS] Virtual environment detected via pyvenv.cfg: %s", pyvenv_cfg)
        return True
    else:
        log.error(
            "[FAIL] No virtual environment detected.  " "Run: source .venv/bin/activate"
        )
        return False


def check_uv_available() -> bool:
    """Confirm uv is on PATH.

    uv is the sole package manager used in this project.  Its absence does
    not prevent the already-activated environment from running, but it will
    block installation of missing dependencies.
    """
    uv_path = shutil.which("uv")

    if uv_path:
        log.info("[PASS] uv found at: %s", uv_path)
        return True
    else:
        log.warning(
            "[WARN] uv not found on PATH.  "
            "Install from https://docs.astral.sh/uv/ to manage dependencies."
        )
        # Warning only — environment may still be usable
        return True


def check_dev_tools() -> bool:
    """Import each development tool and log its version where available."""
    all_passed = True

    for import_name, display_name in DEV_TOOLS:
        try:
            mod = importlib.import_module(import_name)
            version = getattr(mod, "__version__", "version unknown")
            log.info("[PASS] %-12s %s", display_name, version)
        except ImportError as exc:
            log.error("[FAIL] %-12s — ImportError: %s", display_name, exc)
            all_passed = False
        except Exception as exc:  # noqa: BLE001
            log.error("[FAIL] %-12s — Unexpected error: %s", display_name, exc)
            all_passed = False

    return all_passed


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all Phase 1 checks.  Returns 0 on full pass, 1 on any failure."""

    log.info("=" * 70)
    log.info("Phase 1 — Python 3.15 Runtime & Tooling Validation")
    log.info("Author  : Dr. Ceasar Jackson Jr.")
    log.info("Python  : %s", sys.version.split()[0])
    log.info("=" * 70)

    results: dict[str, bool] = {
        "Python version": check_python_version(),
        "Platform": check_platform(),
        "Virtual environment": check_virtual_environment(),
        "uv availability": check_uv_available(),
        "Development tools": check_dev_tools(),
    }

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    log.info("=" * 70)
    log.info("Phase 1 Summary")
    log.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for check_name, result in results.items():
        status = "PASS" if result else "FAIL"
        if result:
            log.info("  [%s] %s", status, check_name)
        else:
            log.error("  [%s] %s", status, check_name)

    log.info("-" * 70)
    if failed == 0:
        log.info("All %d checks passed.  Environment is ready for Phase 2.", passed)
        return 0
    else:
        log.error(
            "%d of %d checks FAILED.  " "Resolve issues above before proceeding.",
            failed,
            len(results),
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
