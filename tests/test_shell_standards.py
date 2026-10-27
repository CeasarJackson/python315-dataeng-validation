#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_shell_standards.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Enforce the Bash standards on every maintained shell script, and prove the
    per-library runners can never report success after a failed step.

    Static rules (all *.sh): env-bash shebang, ``set -Eeuo pipefail``,
    ``IFS=$'\\n\\t'``, an Author line, a documented Exit Codes section, and the
    executable bit.

    Behavioral rules (the five ``*_tests/run_*_validation.sh`` runners): a
    failing interpreter yields exit 1 and no "VALIDATION PASSED" line; DRY_RUN=1
    executes nothing and exits 0; an unknown argument exits 2.

Validation:
    python -m py_compile tests/test_shell_standards.py
    python -m pytest tests/test_shell_standards.py -v

==============================================================================
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".venv", ".venv3151", ".git", "releases", "node_modules", "__pycache__"}


def _shell_scripts() -> list[Path]:
    found = []
    for path in sorted(PROJECT_ROOT.rglob("*.sh")):
        rel = path.relative_to(PROJECT_ROOT)
        if any(part in SKIP_PARTS for part in rel.parts) or ".backup." in path.name:
            continue
        found.append(path)
    return found


SCRIPTS = _shell_scripts()
RUNNERS = [
    p
    for p in SCRIPTS
    if p.name.startswith("run_") and p.name.endswith("_validation.sh")
]


def _id(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def test_shell_scripts_were_discovered() -> None:
    assert (
        len(SCRIPTS) >= 7
    ), "expected release.sh, validate_all.sh and the five runners"
    assert len(RUNNERS) == 5


@pytest.mark.parametrize("script", SCRIPTS, ids=_id)
def test_static_shell_standards(script: Path) -> None:
    text = script.read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:60])
    name = _id(script)
    assert text.startswith(
        "#!/usr/bin/env bash\n"
    ), f"{name}: shebang must be #!/usr/bin/env bash"
    assert re.search(
        r"^set -Eeuo pipefail$", text, re.M
    ), f"{name}: needs 'set -Eeuo pipefail'"
    assert "IFS=$'\\n\\t'" in text, f"{name}: needs IFS=$'\\n\\t'"
    assert "Author" in head, f"{name}: banner needs an Author line"
    assert re.search(
        r"Exit Codes", head
    ), f"{name}: banner needs an 'Exit Codes' section"
    assert os.access(script, os.X_OK), f"{name}: run 'chmod +x {name}'"


def _run(
    script: Path, env_extra: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NO_COLOR": "1", **env_extra}
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


needs_bash = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash not available"
)


@needs_bash
@pytest.mark.parametrize("script", RUNNERS, ids=_id)
def test_runner_failing_step_is_never_reported_as_pass(
    script: Path, tmp_path: Path
) -> None:
    # A stand-in interpreter that always fails. This is the regression test for
    # the bug where `set -e` was silently disabled inside a function called
    # from `if !`, letting a failed step fall through to "VALIDATION PASSED".
    fake = tmp_path / "failing_python"
    fake.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    fake.chmod(0o755)
    result = _run(script, {"PYTHON": str(fake)})
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "VALIDATION PASSED" not in out
    assert "VALIDATION FAILED" in out


@needs_bash
@pytest.mark.parametrize("script", RUNNERS, ids=_id)
def test_runner_dry_run_executes_nothing(script: Path, tmp_path: Path) -> None:
    # If DRY_RUN executed a step, this marker file would appear.
    marker = tmp_path / "ran"
    fake = tmp_path / "marker_python"
    fake.write_text(
        f"#!/bin/sh\ncase \"$1\" in --version) echo 'Python 0';; *) : > '{marker}';; esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    result = _run(script, {"PYTHON": str(fake), "DRY_RUN": "1"})
    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists(), "DRY_RUN=1 must not execute any step"
    assert "DRY RUN COMPLETE" in result.stdout
    # Each echoed command must be ONE line. With IFS=$'\n\t', "${cmd[*]}" joins
    # words with a newline unless the function resets IFS locally.
    echoed = [ln for ln in result.stdout.splitlines() if ln.startswith("+ ")]
    assert echoed, "runner must echo each command"
    assert all(ln.endswith(".py") for ln in echoed), echoed


@needs_bash
@pytest.mark.parametrize("script", RUNNERS, ids=_id)
def test_runner_rejects_unknown_argument(script: Path) -> None:
    result = _run(script, {}, "--bogus")
    assert result.returncode == 2
    assert "Unknown argument" in result.stderr
