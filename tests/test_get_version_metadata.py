#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_get_version_metadata.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify that generate_report.get_version() reports a missing package, a
    broken install (Python 3.15 MetadataNotFound) and a healthy package
    differently instead of crashing the report.

Validation:
    python -m py_compile tests/test_get_version_metadata.py
    python -m pytest tests/test_get_version_metadata.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)


def load_generator() -> ModuleType:
    """Load generate_report.py as an importable test module."""
    spec = importlib.util.spec_from_file_location("generate_report_gv", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installed_package_returns_its_version() -> None:
    version = load_generator().get_version("pytest")
    assert version not in {"not installed", "metadata missing"}


def test_missing_package_is_reported_as_not_installed() -> None:
    assert load_generator().get_version("no-such-package-xyz-315") == "not installed"


def test_metadata_not_found_is_reported_not_raised(monkeypatch) -> None:
    """MetadataNotFound is a FileNotFoundError, not a PackageNotFoundError."""

    class FakeMetadataNotFound(FileNotFoundError):
        pass

    def raise_metadata_not_found(_package: str) -> str:
        raise FakeMetadataNotFound("no metadata file")

    assert not issubclass(FakeMetadataNotFound, importlib.metadata.PackageNotFoundError)
    monkeypatch.setattr(importlib.metadata, "version", raise_metadata_not_found)
    assert load_generator().get_version("anything") == "metadata missing"


@pytest.mark.skipif(
    sys.version_info < (3, 15), reason="MetadataNotFound is new in 3.15"
)
def test_real_dist_info_without_metadata_file(tmp_path, monkeypatch) -> None:
    """Exercise the real interpreter behavior on 3.15."""
    (tmp_path / "ghostpkg315-1.0.dist-info").mkdir()
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    assert load_generator().get_version("ghostpkg315") == "metadata missing"
