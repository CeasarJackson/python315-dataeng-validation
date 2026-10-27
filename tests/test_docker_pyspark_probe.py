#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_docker_pyspark_probe.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    The report generator probes PySpark inside a Docker image, so the host
    Python says nothing about what actually ran. Verify that the PASS record
    names the image and the container's own Python version, so a probe that ran
    on 3.14.x can never be mistaken for a 3.15.1 result, and that failures still
    surface as FAIL.

Validation:
    python -m py_compile tests/test_docker_pyspark_probe.py
    python -m pytest tests/test_docker_pyspark_probe.py -v

==============================================================================
"""

from __future__ import annotations

import builtins
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

GENERATOR_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_report.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_report_dpp", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_version = lambda _package: "9.9.9"
    return module


def run_probe(monkeypatch, stdout: str, returncode: int = 0, image: str = "img:test"):
    """Run collect_results with only the Docker PySpark branch live."""
    generator = load_generator()
    monkeypatch.setattr(generator, "probe_package", lambda pkg: ("PASS", "1.0"))
    monkeypatch.setattr(generator, "check_docker_image", lambda _image: True)
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

    real_import = builtins.__import__

    def no_airflow(name, *args, **kwargs):
        if name == "airflow":
            raise ModuleNotFoundError("No module named 'airflow'", name="airflow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_airflow)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=returncode, stdout=stdout, stderr=""
        ),
    )
    return generator.collect_results(docker_image=image)["pyspark"]


def test_pass_records_image_and_container_python(monkeypatch) -> None:
    out = json.dumps({"status": "pass", "version": "4.2.0", "python": "3.15.1"})
    result = run_probe(monkeypatch, out, image="pyarrow-dataeng:py315")
    assert result["status"] == "PASS"
    assert result["version"] == "4.2.0"
    assert "pyarrow-dataeng:py315" in result["note"]
    assert "Python 3.15.1" in result["note"]


def test_old_image_without_python_field_says_unknown(monkeypatch) -> None:
    out = json.dumps({"status": "pass", "version": "4.1.2"})
    result = run_probe(monkeypatch, out)
    assert result["status"] == "PASS"
    assert "Python unknown" in result["note"]


@pytest.mark.parametrize(
    ("stdout", "returncode", "status"),
    [
        (json.dumps({"status": "fail"}), 1, "FAIL"),
        (json.dumps({"status": "pass", "version": "4.2.0"}), 1, "FAIL"),
        ("not json at all", 0, "INCOMPAT"),
    ],
    ids=["probe-failed", "nonzero-exit", "garbled-output"],
)
def test_failures_do_not_become_pass(monkeypatch, stdout, returncode, status) -> None:
    assert run_probe(monkeypatch, stdout, returncode)["status"] == status


def test_py315_image_running_wrong_python_is_a_fail_with_a_reason(monkeypatch) -> None:
    """A probe that passed on 3.14.5 must never count as 3.15.1 evidence."""
    out = json.dumps({"status": "pass", "version": "4.1.2", "python": "3.14.5"})
    result = run_probe(monkeypatch, out, image="pyarrow-dataeng:py315")
    assert result["status"] == "FAIL"
    assert "3.14.5" in result["reason"]
    assert "3.15.1" in result["reason"]


def test_py315_image_with_no_python_field_is_a_fail(monkeypatch) -> None:
    out = json.dumps({"status": "pass", "version": "4.2.0"})
    result = run_probe(monkeypatch, out, image="pyarrow-dataeng:py315")
    assert result["status"] == "FAIL"
    assert "unknown" in result["reason"]
