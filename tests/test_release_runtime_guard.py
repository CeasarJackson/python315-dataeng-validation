#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_release_runtime_guard.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Test the guard that stops generate_report.py from filing a report under a
    release the running interpreter is not. Without it, a stale virtual
    environment (uv declines to replace an existing venv) can re-measure the old
    Python build and publish the result under the new release name.

    The other generator tests replace this guard with a no-op so they can run on
    any interpreter. This file is the one place the real guard is exercised, and
    it checks the guard fires before any probe runs or any file is written.

Validation:
    python -m py_compile tests/test_release_runtime_guard.py
    python -m pytest tests/test_release_runtime_guard.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import itertools
import logging
import sys
from pathlib import Path

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)
_counter = itertools.count()


def load_generator(monkeypatch):
    """Load generate_report.py as a fresh module for each test."""
    name = f"generate_report_guard_t{next(_counter)}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def pretend_runtime(generator, monkeypatch, version: str) -> None:
    monkeypatch.setattr(generator.platform, "python_version", lambda: version)


def test_matching_runtime_passes_silently(monkeypatch, caplog) -> None:
    generator = load_generator(monkeypatch)
    pretend_runtime(generator, monkeypatch, "3.15.1")
    with caplog.at_level(logging.DEBUG):
        assert generator.verify_release_matches_runtime("3.15.1") is None
    assert caplog.text == ""


@pytest.mark.parametrize("running", ["3.15.0", "3.14.4", "3.15.1rc1"])
def test_mismatched_runtime_refuses_and_says_how_to_fix(
    monkeypatch, caplog, running
) -> None:
    generator = load_generator(monkeypatch)
    pretend_runtime(generator, monkeypatch, running)
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        generator.verify_release_matches_runtime("3.15.1")
    assert exc.value.code == 1
    # The fix must name the trap that causes the problem: without --clear, uv
    # leaves the old venv in place.
    assert "uv venv --clear --python 3.15.1" in caplog.text
    assert running in caplog.text


def test_override_continues_but_says_the_report_is_not_a_validation(
    monkeypatch, caplog
) -> None:
    generator = load_generator(monkeypatch)
    pretend_runtime(generator, monkeypatch, "3.15.0")
    with caplog.at_level(logging.WARNING):
        assert (
            generator.verify_release_matches_runtime("3.15.1", allow_mismatch=True)
            is None
        )
    assert "NOT a validation of 3.15.1" in caplog.text


def test_main_refuses_a_mismatch_before_probing_or_writing(
    monkeypatch, tmp_path
) -> None:
    generator = load_generator(monkeypatch)
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(generator, "REPORTS", reports)
    pretend_runtime(generator, monkeypatch, "3.15.0")

    # Keep the real logging code path but never write into the repo's logs/.
    real_configure = generator._configure_logging
    monkeypatch.setattr(
        generator,
        "_configure_logging",
        lambda file_logging=True: real_configure(file_logging=False),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("must not probe after a version mismatch")

    monkeypatch.setattr(generator, "collect_results", forbidden)
    monkeypatch.setattr(sys, "argv", ["generate_report.py", "--release", "3.15.1"])

    with pytest.raises(SystemExit) as exc:
        generator.main()
    assert exc.value.code == 1
    assert list(reports.iterdir()) == []  # nothing staged, nothing published
