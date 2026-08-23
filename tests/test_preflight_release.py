#!/usr/bin/env python3
# =============================================================================
# Script: test_preflight_release.py
# Author: Dr. Ceasar Jackson Jr.
# Project: Python 3.15 Data Engineering Validation Suite
# Path: tests/test_preflight_release.py
#
# Purpose:
#   Validate the Python 3.15 release-preflight protections implemented by
#   scripts/preflight_release.py. Tests cover release-version validation,
#   exact runtime matching, interpreter-provider detection, report-directory
#   overwrite protection, and architecture validation.
#
# Usage:
#   .venv/bin/python -m pytest tests/test_preflight_release.py -v
#
# Prerequisites:
#   - Repository development environment is available.
#   - pytest is installed in the selected project interpreter.
#
# Validation:
#   .venv/bin/python -m py_compile tests/test_preflight_release.py
#   .venv/bin/python -m pytest tests/test_preflight_release.py -q
#   .venv/bin/python -m pytest tests -q
#   git diff --check
# =============================================================================

"""Tests for the Python 3.15 release-preflight protections."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "preflight_release.py"

spec = importlib.util.spec_from_file_location(
    "preflight_release",
    MODULE_PATH,
)
assert spec is not None
assert spec.loader is not None

preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_release_format_accepts_rc_release():
    """Verify an RC-style Python 3.15 release identifier is accepted."""
    result = preflight.check_release_format("3.15.0rc2")
    assert result.status == "PASS"


def test_release_format_accepts_final_release():
    """Verify the final Python 3.15.0 release identifier is accepted."""
    result = preflight.check_release_format("3.15.0")
    assert result.status == "PASS"


def test_release_format_rejects_wrong_minor():
    """Verify a non-3.15 release identifier is rejected."""
    result = preflight.check_release_format("3.14.7")
    assert result.status == "FAIL"


def test_runtime_match_requires_exact_version():
    """Verify an RC2 request fails when the runtime is only RC1."""
    result = preflight.check_runtime_match(
        "3.15.0rc2",
        "3.15.0rc1",
    )
    assert result.status == "FAIL"


def test_runtime_match_accepts_exact_version():
    """Verify an exact requested-release/runtime match passes."""
    result = preflight.check_runtime_match(
        "3.15.0rc1",
        "3.15.0rc1",
    )
    assert result.status == "PASS"


def test_provider_detects_python_org():
    """Verify python.org framework installations are identified correctly."""
    provider = preflight.detect_provider(
        "/tmp/project/.venv/bin/python",
        (
            "/Library/Frameworks/Python.framework/"
            "Versions/3.15/bin/python3.15"
        ),
    )
    assert provider == "python.org"


def test_provider_detects_uv():
    """Verify uv-managed standalone Python installations are identified."""
    provider = preflight.detect_provider(
        (
            "/Users/test/.local/share/uv/python/"
            "cpython-3.15.0rc2-macos-aarch64-none/bin/python3.15"
        ),
        (
            "/Users/test/.local/share/uv/python/"
            "cpython-3.15.0rc2-macos-aarch64-none/bin/python3.15"
        ),
    )
    assert provider == "uv"


def test_existing_report_is_protected(tmp_path):
    """Verify populated release-report directories cannot be overwritten."""
    release_dir = tmp_path / "3.15.0rc2"
    release_dir.mkdir()
    (release_dir / "manifest.json").write_text("{}")

    result = preflight.check_report_directory(
        release_dir,
        allow_existing_report=False,
    )

    assert result.status == "FAIL"


def test_existing_report_can_be_explicitly_allowed(tmp_path):
    """Verify historical report inspection can be explicitly authorized."""
    release_dir = tmp_path / "3.15.0rc1"
    release_dir.mkdir()
    (release_dir / "manifest.json").write_text("{}")

    result = preflight.check_report_directory(
        release_dir,
        allow_existing_report=True,
    )

    assert result.status == "WARN"


def test_arm64_architecture_passes():
    """Verify the expected Apple Silicon architecture passes preflight."""
    result = preflight.check_architecture(
        "arm64",
        allow_non_arm64=False,
    )
    assert result.status == "PASS"
