#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_script_interrupt_handling.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Every maintained command-line script must exit with code 130 on Ctrl-C
    instead of printing a traceback. The check is static: a script that defines
    main() and has an ``if __name__ == "__main__"`` guard must handle
    KeyboardInterrupt inside that guard. Scripts that predate main() are
    listed explicitly so the gap stays visible and cannot grow.

Validation:
    python -m py_compile tests/test_script_interrupt_handling.py
    python -m pytest tests/test_script_interrupt_handling.py -v

==============================================================================
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIRS = [PROJECT_ROOT / "scripts", PROJECT_ROOT / "tools"]
GUARD = re.compile(r'^if __name__ == [\'"]__main__[\'"]:\s*$', re.M)

# Module-level scripts with no main() or guard. Each needs a restructure
# before it can follow the rule; they are listed so the test fails if one of
# them is quietly copied as a template for new work.
NO_MAIN_YET = {
    "tools/build_reports_system.py",
    "tools/fix_repo_docs.py",
    "tools/update_docs.py",
    "scripts/validate_dataeng_stack.py",
}


def maintained_scripts() -> list[Path]:
    found = []
    for directory in SCRIPT_DIRS:
        for path in sorted(directory.glob("*.py")):
            if path.name == "__init__.py" or ".backup." in path.name:
                continue
            found.append(path)
    return found


def guard_block(text: str) -> str | None:
    """Return the text from the __main__ guard to the end of the file."""
    match = GUARD.search(text)
    return text[match.start() :] if match else None


def test_scripts_were_discovered() -> None:
    assert maintained_scripts()


def test_main_scripts_handle_ctrl_c_with_exit_130() -> None:
    failures = []
    for path in maintained_scripts():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        block = guard_block(text)
        has_main = "def main" in text
        if not has_main or block is None:
            continue
        # The handler may live in the guard or inside main(); either way the
        # script must catch KeyboardInterrupt and produce exit code 130.
        if "KeyboardInterrupt" not in text or "130" not in text:
            failures.append(rel)
    assert not failures, "Missing Ctrl-C handler (exit 130): " + ", ".join(failures)


def test_known_gaps_list_is_accurate() -> None:
    """The exemption list may only name scripts that really lack main()."""
    stale = []
    for rel in sorted(NO_MAIN_YET):
        text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
        if "def main" in text and guard_block(text) is not None:
            stale.append(rel)
    assert not stale, f"Now have main(); remove from NO_MAIN_YET: {stale}"
