#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_package_classification.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Pin how generate_report classifies pyarrow, dask.dataframe, mlflow and ray:
    a missing module is a SKIP or BLOCKED (no cp315 wheel), while a package that
    is present but fails to import is an INCOMPAT and is never hidden as absent.
    Also pins the order of the results, which is the key order of the manifest,
    and the severity each status is logged at.

Validation:
    python -m py_compile tests/test_package_classification.py
    python -m pytest tests/test_package_classification.py -v

==============================================================================
"""

from __future__ import annotations

import builtins
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)


def load_generator() -> ModuleType:
    """Load generate_report.py with a deterministic get_version."""
    spec = importlib.util.spec_from_file_location("generate_report_pc", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_version = lambda _package: "9.9.9"
    return module


def break_import(monkeypatch, target: str, exc: BaseException) -> None:
    """Make ``import <target>`` raise ``exc`` while every other import works."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == target:
            raise exc
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def absent(name: str) -> ModuleNotFoundError:
    return ModuleNotFoundError(f"No module named {name!r}", name=name)


def install_fake(monkeypatch, name: str, **attrs) -> None:
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)


# --- pyarrow ---------------------------------------------------------------


def test_pyarrow_present_is_pass(monkeypatch) -> None:
    install_fake(monkeypatch, "pyarrow", __version__="26.0.0")
    result, detail = load_generator()._probe_pyarrow()
    assert result == {"status": "PASS", "version": "26.0.0"}
    assert detail == "26.0.0"


def test_pyarrow_absent_is_blocked(monkeypatch) -> None:
    break_import(monkeypatch, "pyarrow", absent("pyarrow"))
    result, detail = load_generator()._probe_pyarrow()
    assert result["status"] == "BLOCKED"
    assert result["version"] == "unavailable"
    assert "cp315" in result["reason"]
    assert detail == "no cp315 wheels"


def test_pyarrow_broken_import_is_incompat_not_blocked(monkeypatch) -> None:
    break_import(monkeypatch, "pyarrow", ImportError("undefined symbol: arrow_foo"))
    result, _ = load_generator()._probe_pyarrow()
    assert result["status"] == "INCOMPAT"
    assert result["version"] == "9.9.9"
    assert "undefined symbol" in result["reason"]


# --- dask.dataframe --------------------------------------------------------


def test_dask_present_is_pass(monkeypatch) -> None:
    install_fake(monkeypatch, "dask")
    install_fake(monkeypatch, "dask.dataframe")
    result, _ = load_generator()._probe_dask()
    assert result == {"status": "PASS", "version": "9.9.9"}


def test_dask_missing_pyarrow_is_incompat(monkeypatch) -> None:
    break_import(monkeypatch, "dask.dataframe", absent("pyarrow"))
    result, detail = load_generator()._probe_dask()
    assert result["status"] == "INCOMPAT"
    assert result["reason"] == "runtime pyarrow dep"
    assert detail == "pyarrow dep"


def test_dask_absent_is_skip(monkeypatch) -> None:
    break_import(monkeypatch, "dask.dataframe", absent("dask"))
    result, _ = load_generator()._probe_dask()
    assert result == {"status": "SKIP", "version": "not installed"}


def test_dask_other_import_failure_is_incompat_not_skip(monkeypatch) -> None:
    break_import(monkeypatch, "dask.dataframe", absent("toolz"))
    result, _ = load_generator()._probe_dask()
    assert result["status"] == "INCOMPAT"
    assert "toolz" in result["reason"]


# --- mlflow ----------------------------------------------------------------


def test_mlflow_present_is_pass(monkeypatch) -> None:
    install_fake(monkeypatch, "mlflow")
    result, _ = load_generator()._probe_mlflow()
    assert result == {"status": "PASS", "version": "9.9.9"}


@pytest.mark.parametrize(
    "exc",
    [absent("pyarrow"), ImportError("opentelemetry sdk mismatch")],
    ids=["pyarrow", "opentelemetry"],
)
def test_mlflow_known_blockers_are_incompat(monkeypatch, exc) -> None:
    break_import(monkeypatch, "mlflow", exc)
    result, detail = load_generator()._probe_mlflow()
    assert result["status"] == "INCOMPAT"
    assert result["reason"] == "pyarrow hard dep"
    assert detail == "pyarrow dep"


def test_mlflow_absent_is_skip(monkeypatch) -> None:
    break_import(monkeypatch, "mlflow", absent("mlflow"))
    result, _ = load_generator()._probe_mlflow()
    assert result == {"status": "SKIP", "version": "not installed"}


@pytest.mark.parametrize(
    "exc", [absent("sqlalchemy"), RuntimeError("boom")], ids=["dependency", "runtime"]
)
def test_mlflow_other_failure_is_incompat_not_skip(monkeypatch, exc) -> None:
    break_import(monkeypatch, "mlflow", exc)
    result, _ = load_generator()._probe_mlflow()
    assert result["status"] == "INCOMPAT"
    assert str(exc.args[0]) in result["reason"] or str(exc) in result["reason"]


# --- ray -------------------------------------------------------------------


def test_ray_present_is_pass(monkeypatch) -> None:
    install_fake(monkeypatch, "ray")
    result, _ = load_generator()._probe_ray()
    assert result == {"status": "PASS", "version": "9.9.9"}


def test_ray_absent_is_blocked(monkeypatch) -> None:
    break_import(monkeypatch, "ray", absent("ray"))
    result, detail = load_generator()._probe_ray()
    assert result["status"] == "BLOCKED"
    assert detail == "no cp315 wheels"


def test_ray_broken_import_is_incompat_not_blocked(monkeypatch) -> None:
    break_import(monkeypatch, "ray", ImportError("libray.so: bad ELF header"))
    result, _ = load_generator()._probe_ray()
    assert result["status"] == "INCOMPAT"
    assert "bad ELF header" in result["reason"]


# --- ordering and logging --------------------------------------------------


def test_collect_results_key_order_is_manifest_order(monkeypatch) -> None:
    """Result order becomes manifest key order, so it must not drift."""
    generator = load_generator()
    monkeypatch.setattr(generator, "probe_package", lambda pkg: ("PASS", "1.0"))
    monkeypatch.setattr(generator, "check_docker_image", lambda _image: False)
    for name in (
        "_probe_pyarrow",
        "_probe_dask",
        "_probe_prefect",
        "_probe_mlflow",
        "_probe_ray",
    ):
        monkeypatch.setattr(
            generator, name, lambda: ({"status": "SKIP", "version": "x"}, "")
        )
    break_import(monkeypatch, "airflow", absent("airflow"))
    keys = list(generator.collect_results())
    assert keys[-7:] == [
        "pyarrow",
        "dask.dataframe",
        "prefect",
        "mlflow",
        "ray",
        "pyspark",
        "apache-airflow",
    ]


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.parametrize(
    ("status", "level"),
    [
        ("PASS", logging.INFO),
        ("FAIL", logging.ERROR),
        ("INCOMPAT", logging.WARNING),
        ("BLOCKED", logging.WARNING),
        ("SKIP", logging.WARNING),
        ("UNKNOWN", logging.WARNING),
    ],
)
def test_log_result_severity_matches_status(status, level) -> None:
    generator = load_generator()
    capture = _Capture()
    generator.LOG.addHandler(capture)
    previous_level = generator.LOG.level
    generator.LOG.setLevel(logging.DEBUG)
    try:
        generator._log_result("pkg", status, "detail")
    finally:
        generator.LOG.removeHandler(capture)
        generator.LOG.setLevel(previous_level)
    assert [(r.levelno, r.getMessage()) for r in capture.records] == [
        (level, f"pkg: {status} (detail)")
    ]
