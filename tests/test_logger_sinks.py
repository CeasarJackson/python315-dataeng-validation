#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_logger_sinks.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Verify the shared logger's sinks: a console-only mode that writes nothing to
    disk (so a dry run is truly write-free), best-effort file logging that never
    crashes on a read-only location, a plain-text file with no ANSI escapes, and a
    console stream that follows the current sys.stdout.

Validation:
    python -m py_compile tests/test_logger_sinks.py
    python -m pytest tests/test_logger_sinks.py -v

==============================================================================
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import itertools
import logging
from pathlib import Path
from types import ModuleType

import pytest

LOGGER_PATH = Path(__file__).resolve().parent.parent / "scripts" / "logger.py"
_counter = itertools.count()


def fresh_logger_module(logs_dir: Path) -> ModuleType:
    """Load logger.py fresh so its registry and log directory are isolated."""
    spec = importlib.util.spec_from_file_location(
        f"logger_sink_{next(_counter)}", LOGGER_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._LOGS_DIR = logs_dir
    return module


@pytest.fixture
def logger_name():
    name = f"sink_test_{next(_counter)}"
    yield name
    logger = logging.getLogger(name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_console_only_writes_nothing_to_disk(tmp_path, logger_name) -> None:
    logs = tmp_path / "logs"
    module = fresh_logger_module(logs)
    logger = module.get_logger(logger_name, file_logging=False)
    logger.info("hello")
    assert not logs.exists()
    assert not any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_file_sink_is_plain_text(tmp_path, logger_name, monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    logs = tmp_path / "logs"
    module = fresh_logger_module(logs)
    logger = module.get_logger(logger_name)
    logger.warning("something happened")
    for handler in logger.handlers:
        handler.flush()
    text = (logs / f"{logger_name}.log").read_text(encoding="utf-8")
    assert "something happened" in text
    assert "\x1b" not in text


def test_unwritable_log_dir_downgrades_to_console_only(tmp_path, logger_name) -> None:
    blocker = tmp_path / "not_a_directory"
    blocker.write_text("a file where the log directory should be", encoding="utf-8")
    module = fresh_logger_module(blocker / "logs")  # mkdir fails: parent is a file
    logger = module.get_logger(logger_name)  # must not raise
    assert not any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_console_stream_follows_current_stdout(tmp_path, logger_name) -> None:
    module = fresh_logger_module(tmp_path / "logs")
    logger = module.get_logger(logger_name, file_logging=False)
    first, second = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(first):
        logger.info("one")
    with contextlib.redirect_stdout(second):
        logger.info("two")
    assert "one" in first.getvalue() and "two" not in first.getvalue()
    assert "two" in second.getvalue()


def test_no_ansi_when_output_is_not_a_terminal(tmp_path, logger_name) -> None:
    pytest.importorskip("colorlog")
    module = fresh_logger_module(tmp_path / "logs")
    logger = module.get_logger(logger_name, file_logging=False)
    buffer = io.StringIO()  # StringIO.isatty() is False, like a pipe
    with contextlib.redirect_stdout(buffer):
        logger.error("not a tty")
    assert "not a tty" in buffer.getvalue()
    assert "\x1b" not in buffer.getvalue()
