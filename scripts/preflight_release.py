#!/usr/bin/env python3
# =============================================================================
# Script: preflight_release.py
# Author: Dr. Ceasar Jackson Jr.
# Project: Python 3.15 Data Engineering Validation Suite
# Path: scripts/preflight_release.py
#
# Purpose:
#   Validate release-cycle prerequisites before Python compatibility testing or
#   report generation begins. The preflight is intentionally stdlib-only so it
#   can run against a newly installed CPython interpreter before project
#   dependencies have been installed.
#
# Key protections:
#   - Requested release must exactly match the running interpreter.
#   - Architecture must be Apple Silicon ARM64/aarch64 unless overridden.
#   - Git worktree must be clean unless explicitly overridden.
#   - Active release report directories cannot already contain results unless
#     explicitly permitted for historical verification.
#   - Interpreter provenance, Git SHA, uv version, architecture, and runtime
#     identity are captured for reproducibility.
#   - Existing quarantined artifacts are reported as warnings, never mistaken
#     for valid release results.
#
# Usage:
#   .venv/bin/python scripts/preflight_release.py --release 3.15.0rc1 \
#       --allow-existing-report
#
#   /path/to/python3.15 scripts/preflight_release.py --release 3.15.0rc2
#
#   /path/to/python3.15 scripts/preflight_release.py \
#       --release 3.15.0rc2 \
#       --json
#
# Exit codes:
#   0  Preflight passed.
#   1  One or more preflight checks failed.
#   2  Invalid command-line usage.
#
# Validation:
#   python -m py_compile scripts/preflight_release.py
#   python -m pytest tests/test_preflight_release.py -q
#   python scripts/preflight_release.py --help
# =============================================================================

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "reports"
QUARANTINE_DIR = REPORTS_DIR / "_quarantine"

RELEASE_PATTERN = re.compile(
    r"^3\.15\.0(?:a\d+|b\d+|rc\d+)?$"
)

VALID_ARM_ARCHITECTURES = {"arm64", "aarch64"}


@dataclass
class CheckResult:
    """One preflight check result."""

    name: str
    status: str
    message: str


@dataclass
class PreflightResult:
    """Complete preflight result and environment provenance."""

    requested_release: str
    python_runtime: str
    python_executable: str
    python_base_executable: str
    interpreter_provider: str
    architecture: str
    platform: str
    git_sha: str
    git_branch: str
    git_dirty: bool
    uv_version: str
    report_directory: str
    report_directory_exists: bool
    quarantine_matches: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.status != "FAIL" for check in self.checks)


def run_command(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
) -> tuple[int, str]:
    """Run a command and return (return_code, combined_output)."""

    try:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError as exc:
        return 127, str(exc)

    return completed.returncode, completed.stdout.strip()


def runtime_version() -> str:
    """Return the exact CPython release identifier for the running interpreter."""

    return platform.python_version()


def detect_base_executable() -> str:
    """Return the underlying base interpreter path when available."""

    base = getattr(sys, "_base_executable", None)
    if base:
        return str(Path(base).expanduser().resolve())

    return str(Path(sys.executable).expanduser().resolve())


def detect_provider(executable: str, base_executable: str) -> str:
    """Infer interpreter provenance from executable paths."""

    combined = f"{executable}\n{base_executable}".lower()

    if "/.local/share/uv/python/" in combined:
        return "uv"
    if "/library/frameworks/python.framework/" in combined:
        return "python.org"
    if "/opt/homebrew/" in combined:
        return "homebrew"
    if "miniforge" in combined or "conda" in combined:
        return "conda"
    if "/.venv" in combined or "/venv/" in combined:
        return "virtualenv"

    return "unknown"


def git_metadata() -> tuple[str, str, bool]:
    """Return Git SHA, branch, and dirty state."""

    sha_rc, sha = run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
    )
    branch_rc, branch = run_command(
        ["git", "branch", "--show-current"],
        cwd=REPO_ROOT,
    )
    status_rc, status = run_command(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
    )

    if sha_rc != 0:
        sha = "<unavailable>"
    if branch_rc != 0 or not branch:
        branch = "<detached-or-unavailable>"

    dirty = status_rc != 0 or bool(status.strip())

    return sha, branch, dirty


def detect_uv_version() -> str:
    """Return uv version or a stable unavailable marker."""

    uv = shutil.which("uv")
    if not uv:
        return "<unavailable>"

    rc, output = run_command([uv, "--version"])
    if rc != 0 or not output:
        return "<unavailable>"

    return output.splitlines()[0]


def quarantine_matches(release: str) -> list[str]:
    """Find quarantined directories whose names reference the release."""

    if not QUARANTINE_DIR.is_dir():
        return []

    matches = [
        path.name
        for path in QUARANTINE_DIR.iterdir()
        if path.is_dir() and release in path.name
    ]
    return sorted(matches)


def check_release_format(release: str) -> CheckResult:
    """Validate the requested Python 3.15 release identifier."""

    if RELEASE_PATTERN.fullmatch(release):
        return CheckResult(
            "release_format",
            "PASS",
            f"Release identifier is valid: {release}",
        )

    return CheckResult(
        "release_format",
        "FAIL",
        (
            f"Invalid release identifier: {release!r}. "
            "Expected a Python 3.15 release such as 3.15.0b4, "
            "3.15.0rc1, 3.15.0rc2, or 3.15.0."
        ),
    )


def check_runtime_match(release: str, runtime: str) -> CheckResult:
    """Require exact requested-release/runtime equality."""

    if release == runtime:
        return CheckResult(
            "runtime_match",
            "PASS",
            f"Requested release matches interpreter runtime: {runtime}",
        )

    return CheckResult(
        "runtime_match",
        "FAIL",
        (
            f"Requested release {release} does not match running "
            f"interpreter {runtime}."
        ),
    )


def check_architecture(
    architecture: str,
    *,
    allow_non_arm64: bool,
) -> CheckResult:
    """Validate expected Apple Silicon architecture."""

    normalized = architecture.lower()

    if normalized in VALID_ARM_ARCHITECTURES:
        return CheckResult(
            "architecture",
            "PASS",
            f"Architecture is {architecture}.",
        )

    if allow_non_arm64:
        return CheckResult(
            "architecture",
            "WARN",
            (
                f"Architecture is {architecture}; continuing because "
                "--allow-non-arm64 was supplied."
            ),
        )

    return CheckResult(
        "architecture",
        "FAIL",
        (
            f"Unexpected architecture: {architecture}. "
            "Expected arm64/aarch64."
        ),
    )


def check_git_clean(
    dirty: bool,
    *,
    allow_dirty: bool,
) -> CheckResult:
    """Require a clean Git worktree unless explicitly overridden."""

    if not dirty:
        return CheckResult(
            "git_worktree",
            "PASS",
            "Git working tree is clean.",
        )

    if allow_dirty:
        return CheckResult(
            "git_worktree",
            "WARN",
            (
                "Git working tree is dirty; continuing because "
                "--allow-dirty was supplied."
            ),
        )

    return CheckResult(
        "git_worktree",
        "FAIL",
        (
            "Git working tree is dirty. Commit/stash changes or rerun "
            "with --allow-dirty for deliberate development testing."
        ),
    )


def check_report_directory(
    release_dir: Path,
    *,
    allow_existing_report: bool,
) -> CheckResult:
    """Protect active release results from accidental overwrite."""

    if not release_dir.exists():
        return CheckResult(
            "report_directory",
            "PASS",
            f"Active report directory does not exist: {release_dir}",
        )

    existing_files = sorted(
        path.name for path in release_dir.iterdir()
    )

    if not existing_files:
        return CheckResult(
            "report_directory",
            "PASS",
            f"Active report directory exists but is empty: {release_dir}",
        )

    if allow_existing_report:
        return CheckResult(
            "report_directory",
            "WARN",
            (
                f"Active report directory already contains "
                f"{len(existing_files)} item(s); continuing because "
                "--allow-existing-report was supplied."
            ),
        )

    return CheckResult(
        "report_directory",
        "FAIL",
        (
            f"Active report directory already contains results: "
            f"{release_dir}. Refusing to overwrite historical evidence."
        ),
    )


def build_result(args: argparse.Namespace) -> PreflightResult:
    """Collect provenance and execute all checks."""

    release = args.release
    runtime = runtime_version()
    executable = str(Path(sys.executable).expanduser().resolve())
    base_executable = detect_base_executable()
    provider = detect_provider(executable, base_executable)
    architecture = platform.machine()
    platform_text = platform.platform()
    git_sha, git_branch, dirty = git_metadata()
    uv_version = detect_uv_version()
    release_dir = REPORTS_DIR / release
    quarantined = quarantine_matches(release)

    checks = [
        check_release_format(release),
        check_runtime_match(release, runtime),
        check_architecture(
            architecture,
            allow_non_arm64=args.allow_non_arm64,
        ),
        check_git_clean(
            dirty,
            allow_dirty=args.allow_dirty,
        ),
        check_report_directory(
            release_dir,
            allow_existing_report=args.allow_existing_report,
        ),
    ]

    if quarantined:
        checks.append(
            CheckResult(
                "quarantine_history",
                "WARN",
                (
                    "Historical quarantined artifact(s) reference this "
                    f"release: {', '.join(quarantined)}"
                ),
            )
        )
    else:
        checks.append(
            CheckResult(
                "quarantine_history",
                "PASS",
                "No quarantined artifacts reference this release.",
            )
        )

    return PreflightResult(
        requested_release=release,
        python_runtime=runtime,
        python_executable=executable,
        python_base_executable=base_executable,
        interpreter_provider=provider,
        architecture=architecture,
        platform=platform_text,
        git_sha=git_sha,
        git_branch=git_branch,
        git_dirty=dirty,
        uv_version=uv_version,
        report_directory=str(release_dir),
        report_directory_exists=release_dir.exists(),
        quarantine_matches=quarantined,
        checks=checks,
    )


def print_human(result: PreflightResult) -> None:
    """Render a readable terminal report."""

    print("=" * 72)
    print(" PYTHON 3.15 RELEASE PREFLIGHT")
    print("=" * 72)

    print(f"Requested release    : {result.requested_release}")
    print(f"Python runtime       : {result.python_runtime}")
    print(f"Python executable    : {result.python_executable}")
    print(f"Base executable      : {result.python_base_executable}")
    print(f"Interpreter provider : {result.interpreter_provider}")
    print(f"Architecture         : {result.architecture}")
    print(f"Git SHA              : {result.git_sha}")
    print(f"Git branch           : {result.git_branch}")
    print(f"Git dirty            : {result.git_dirty}")
    print(f"uv                    : {result.uv_version}")
    print(f"Report directory     : {result.report_directory}")

    print()
    print("Checks")
    print("-" * 72)

    for check in result.checks:
        print(f"{check.status:4}  {check.name:20}  {check.message}")

    print()
    print("=" * 72)
    if result.passed:
        print(" PREFLIGHT PASSED")
    else:
        print(" PREFLIGHT FAILED")
    print("=" * 72)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate interpreter and repository prerequisites before a "
            "Python 3.15 compatibility release cycle."
        )
    )
    parser.add_argument(
        "--release",
        required=True,
        help="Expected Python release, for example 3.15.0rc2.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow a dirty Git worktree for deliberate development testing.",
    )
    parser.add_argument(
        "--allow-existing-report",
        action="store_true",
        help=(
            "Allow an existing populated reports/<release>/ directory. "
            "Use for historical verification only."
        ),
    )
    parser.add_argument(
        "--allow-non-arm64",
        action="store_true",
        help="Allow validation on a non-arm64/aarch64 architecture.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of terminal output.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point."""

    args = parse_args(argv)
    result = build_result(args)

    if args.json:
        payload = asdict(result)
        payload["passed"] = result.passed
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
