#!/usr/bin/env python3
"""
==============================================================================
PLACEHOLDER / SAFETY REDIRECT
==============================================================================
Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Prevent accidental edits or execution of the wrong sync_readiness.py file.

Active Script:
    tools/sync_readiness.py

Usage:
    python tools/sync_readiness.py

Validation:
    python -m py_compile sync_readiness.py
    python sync_readiness.py
    echo $?
    tail -5 ~/Logs/python315_test/sync_readiness_redirect.log
    python -m py_compile tools/sync_readiness.py
    python tools/sync_readiness.py --dry-run

Logging:
    Screen output and log output are both generated.
    Log file:
        ~/Logs/python315_test/sync_readiness_redirect.log
==============================================================================
"""

from datetime import datetime
from pathlib import Path

RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"

LOG_DIR = Path.home() / "Logs" / "python315_test"
LOG_FILE = LOG_DIR / "sync_readiness_redirect.log"


def log_error(message: str) -> None:
    """Write error message to screen and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{RED}[ERROR]{NC} {message}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] [ERROR] {message}\n")


if __name__ == "__main__":
    log_error("Use tools/sync_readiness.py instead of repo-root sync_readiness.py")
    raise SystemExit(1)
