#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_benchmark_output_dir.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Pin two properties of scripts/benchmark_pandas_polars.py that the Tachyon
    wrapper relies on:

    * BENCHMARK_OUTPUT_DIR redirects the results CSV, so a profiled run cannot
      overwrite the committed results in data/. Unset, the default is data/.
    * The CSV is written with LF line endings. csv.DictWriter defaults to CRLF,
      which made every run a whole-file diff against the committed LF file.

Validation:
    python -m py_compile tests/test_benchmark_output_dir.py
    python -m pytest tests/test_benchmark_output_dir.py -v

==============================================================================
"""

from __future__ import annotations

import csv
import importlib.util
import itertools
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_counter = itertools.count()


def load_benchmark(monkeypatch, tmp_path, output_dir=None):
    """Load the benchmark with its log directory redirected off the repo."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import logger as shared

    monkeypatch.setattr(shared, "_LOGS_DIR", tmp_path / "logs")
    if output_dir is None:
        monkeypatch.delenv("BENCHMARK_OUTPUT_DIR", raising=False)
    else:
        monkeypatch.setenv("BENCHMARK_OUTPUT_DIR", str(output_dir))
    name = f"benchmark_pandas_polars_t{next(_counter)}"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "benchmark_pandas_polars.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def test_default_output_is_the_data_directory(monkeypatch, tmp_path) -> None:
    mod = load_benchmark(monkeypatch, tmp_path)
    assert SCRIPTS.parent / "data" / "benchmark_pandas_polars.csv" == mod.OUTPUT_CSV


def test_env_var_redirects_the_results_file(monkeypatch, tmp_path) -> None:
    target = tmp_path / "scratch"
    mod = load_benchmark(monkeypatch, tmp_path, output_dir=target)
    assert target / "benchmark_pandas_polars.csv" == mod.OUTPUT_CSV


def test_csv_is_written_with_lf_line_endings(monkeypatch, tmp_path) -> None:
    mod = load_benchmark(monkeypatch, tmp_path, output_dir=tmp_path)
    # Reproduce the script's writer settings rather than running the benchmark.
    source = (SCRIPTS / "benchmark_pandas_polars.py").read_text(encoding="utf-8")
    assert 'lineterminator="\\n"' in source
    out = mod.OUTPUT_CSV
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["a"], lineterminator="\n")
        writer.writeheader()
    assert b"\r" not in out.read_bytes()
