#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_fix_repository_headers.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    scripts/fix_repository_headers.py rewrites source files, so it must be
    safe: keep the shebang on line 1, back up before writing, write nothing
    under --check or --dry-run, and report problems through its exit code.

Validation:
    python -m py_compile tests/test_fix_repository_headers.py
    python -m pytest tests/test_fix_repository_headers.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_counter = itertools.count()

BARE = "import os\n\nprint(os.getcwd())\n"
COMPLETE = '"""\nAuthor: x\n\nPurpose:\ny\n\nValidation:\nz\n"""\n'


def load_tool(monkeypatch, tmp_path: Path, targets: list[str]) -> ModuleType:
    """Load the script with logs and its target list pointed at tmp_path."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import logger as shared

    monkeypatch.setattr(shared, "_LOGS_DIR", tmp_path / "logs")
    name = f"fix_repository_headers_t{next(_counter)}"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "fix_repository_headers.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "TARGETS", targets)
    return module


def backups(tmp_path: Path) -> list[Path]:
    return list(tmp_path.glob("*.backup.*"))


def test_header_goes_after_the_shebang(monkeypatch, tmp_path) -> None:
    tool = load_tool(monkeypatch, tmp_path, ["a.py"])
    out = tool.insert_header("#!/usr/bin/env python3\nimport os\n", '"""hdr"""\n\n')
    assert out.splitlines()[0] == "#!/usr/bin/env python3"
    assert out.splitlines()[1] == '"""hdr"""'


def test_header_goes_first_when_there_is_no_shebang(monkeypatch, tmp_path) -> None:
    tool = load_tool(monkeypatch, tmp_path, ["a.py"])
    assert tool.insert_header("import os\n", '"""hdr"""\n\n').startswith('"""hdr"""')


def test_real_run_backs_up_then_writes_and_keeps_shebang(monkeypatch, tmp_path) -> None:
    target = tmp_path / "a.py"
    original = "#!/usr/bin/env python3\n" + BARE
    target.write_text(original, encoding="utf-8")
    tool = load_tool(monkeypatch, tmp_path, ["a.py"])

    assert tool.main([]) == 0

    text = target.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "#!/usr/bin/env python3"
    assert not tool.missing_markers(text)
    saved = backups(tmp_path)
    assert len(saved) == 1
    assert saved[0].read_text(encoding="utf-8") == original  # undo is one mv away


def test_dry_run_writes_nothing_and_exits_zero(monkeypatch, tmp_path) -> None:
    target = tmp_path / "a.py"
    target.write_text(BARE, encoding="utf-8")
    tool = load_tool(monkeypatch, tmp_path, ["a.py"])

    assert tool.main(["--dry-run"]) == 0

    assert target.read_text(encoding="utf-8") == BARE
    assert backups(tmp_path) == []


@pytest.mark.parametrize(
    ("content", "expected"), [(BARE, 1), (COMPLETE + BARE, 0)], ids=["missing", "ok"]
)
def test_check_mode_exit_code_and_no_writes(
    monkeypatch, tmp_path, content, expected
) -> None:
    target = tmp_path / "a.py"
    target.write_text(content, encoding="utf-8")
    tool = load_tool(monkeypatch, tmp_path, ["a.py"])

    assert tool.main(["--check"]) == expected

    assert target.read_text(encoding="utf-8") == content
    assert backups(tmp_path) == []


def test_missing_target_is_skipped_not_fatal(monkeypatch, tmp_path) -> None:
    tool = load_tool(monkeypatch, tmp_path, ["does_not_exist.py"])
    assert tool.main([]) == 0


def test_unreadable_target_fails_with_exit_1(monkeypatch, tmp_path) -> None:
    (tmp_path / "bad.py").write_bytes(b"\xff\xfe not utf-8")
    tool = load_tool(monkeypatch, tmp_path, ["bad.py"])
    # A non-UTF-8 file must surface as a clean failure, not a traceback.
    assert tool.main([]) == 1
