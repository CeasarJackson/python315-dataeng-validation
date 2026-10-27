#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_profile_with_tachyon.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify the Tachyon wrapper without running the profiler: command assembly,
    input validation, the "Tachyon unavailable" path, failure reporting and the
    post-run output check. A real profiling run needs Python 3.15 and, on macOS,
    possibly elevated permission, so it is exercised by hand on the Mac.

Validation:
    python -m py_compile tests/test_profile_with_tachyon.py
    python -m pytest tests/test_profile_with_tachyon.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import itertools
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_counter = itertools.count()


def load_wrapper(monkeypatch, tmp_path) -> ModuleType:
    """Load the script with its log directory and output directory off the repo."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import logger as shared

    monkeypatch.setattr(shared, "_LOGS_DIR", tmp_path / "logs")
    name = f"profile_with_tachyon_t{next(_counter)}"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "profile_with_tachyon.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(["x"], returncode, stdout, stderr)


def argv(tmp_path, *extra):
    return ["--output-dir", str(tmp_path / "profiles"), *extra]


def test_command_puts_profiler_options_before_the_target(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    target = Path("/repo/scripts/bench.py")
    out = Path("/out/bench.html")
    cmd = mod.build_command(target, "flamegraph", "5k", 30, out, ["--size", "10"])
    assert cmd[1:5] == ["-m", "profiling.sampling", "run", "-r"]
    assert cmd.index("--flamegraph") < cmd.index(str(target))
    assert cmd[-3:] == [str(target), "--size", "10"]
    assert cmd[cmd.index("-d") + 1] == "30"
    assert cmd[cmd.index("-o") + 1] == str(out)


@pytest.mark.parametrize(
    ("fmt", "flag", "ext"),
    [
        ("flamegraph", "--flamegraph", ".html"),
        ("pstats", "--pstats", ".pstats"),
        ("collapsed", "--collapsed", ".collapsed"),
    ],
)
def test_each_format_maps_to_its_flag_and_extension(
    monkeypatch, tmp_path, fmt, flag, ext
) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    out = mod.build_output_path(
        Path("scripts/bench.py"), fmt, tmp_path, "20261026_000000"
    )
    assert out.name == f"bench_20261026_000000{ext}"
    assert mod.FORMATS[fmt][0] == flag


def test_dry_run_runs_nothing_and_succeeds_anywhere(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)

    def boom(*a, **k):
        raise AssertionError("subprocess must not run during --dry-run")

    monkeypatch.setattr(mod.subprocess, "run", boom)
    assert mod.main(argv(tmp_path, "--dry-run")) == 0
    assert not (tmp_path / "profiles").exists()


@pytest.mark.parametrize(
    "bad",
    [
        ["--target", "does_not_exist.py"],
        ["--rate", "fast"],
        ["--duration", "0"],
        ["--rate", "10 -x"],
    ],
)
def test_invalid_input_exits_2_before_anything_runs(monkeypatch, tmp_path, bad) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: pytest.fail("ran"))
    assert mod.main(argv(tmp_path, *bad)) == 2


def test_unavailable_tachyon_exits_3(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "tachyon_available", lambda: (False, "no tachyon here"))
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: pytest.fail("ran"))
    assert mod.main(argv(tmp_path)) == 3


def test_old_python_reports_unavailable(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod.sys, "version_info", (3, 14, 0, "final", 0))
    ok, reason = mod.tachyon_available()
    assert not ok
    assert "3.15" in reason


def test_success_requires_a_nonempty_profile_file(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "tachyon_available", lambda: (True, ""))

    def fake_run(cmd, **kwargs):
        Path(cmd[cmd.index("-o") + 1]).write_text(
            "<html>profile</html>", encoding="utf-8"
        )
        return completed()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.main(argv(tmp_path)) == 0
    assert len(list((tmp_path / "profiles").glob("*.html"))) == 1


def test_clean_exit_with_no_output_file_is_a_failure(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "tachyon_available", lambda: (True, ""))
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: completed())
    assert mod.main(argv(tmp_path)) == 1


def test_profiler_failure_exits_1_and_flags_permission_problems(
    monkeypatch, tmp_path, caplog
) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "tachyon_available", lambda: (True, ""))
    err = completed(1, stderr="task_for_pid failed: Operation not permitted")
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: err)
    mod.log.propagate = True
    with caplog.at_level("WARNING"):
        assert mod.main(argv(tmp_path)) == 1
    assert "permission problem" in caplog.text


def test_timeout_exits_1(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "tachyon_available", lambda: (True, ""))

    def slow(*a, **k):
        raise subprocess.TimeoutExpired("x", 1)

    monkeypatch.setattr(mod.subprocess, "run", slow)
    assert mod.main(argv(tmp_path, "--timeout", "1")) == 1


def test_arguments_after_double_dash_reach_the_target(monkeypatch, tmp_path) -> None:
    mod = load_wrapper(monkeypatch, tmp_path)
    seen = {}
    monkeypatch.setattr(mod, "tachyon_available", lambda: (True, ""))

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        Path(cmd[cmd.index("-o") + 1]).write_text("x", encoding="utf-8")
        return completed()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.main(argv(tmp_path, "--", "--size", "10")) == 0
    assert seen["cmd"][-2:] == ["--size", "10"]
    assert "--" not in seen["cmd"]
