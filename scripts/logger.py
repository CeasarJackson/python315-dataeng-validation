"""
================================================================================
logger.py — Shared Colored Logging Module
================================================================================
Project  : Python 3.15 Data Engineering Validation Suite
Author   : Dr. Ceasar Jackson Jr.
Platform : macOS 26.5 ARM64
Manager  : uv
================================================================================

PURPOSE
-------
Provides a single, consistent logging configuration for all validation and
benchmark scripts in this project. Each script calls `get_logger(__name__)` to
receive a logger that writes:

  1. Colored output to the terminal (stdout) via `colorlog`.
  2. Plain-text, timestamped entries to a rotating log file under logs/.

TERMINAL COLOR SCHEME
---------------------
  DEBUG    → Cyan        — Detailed internals, raw version strings
  INFO     → Green       — Normal progress, [PASS] results
  WARNING  → Yellow      — Soft failures, version mismatches, [SKIP]
  ERROR    → Red         — Hard failures, import errors, exceptions
  CRITICAL → Bold Red    — Fatal conditions requiring immediate attention

LOG FILE FORMAT
---------------
  YYYY-MM-DD HH:MM:SS | LEVEL    | module:lineno — message

ROTATION POLICY
---------------
  Max file size : 5 MB
  Backup count  : 3  (logs/<name>.log, .log.1, .log.2, .log.3)

USAGE
-----
  from logger import get_logger
  log = get_logger(__name__)

  log.debug("raw value: %s", value)
  log.info("[PASS] numpy %s imported", numpy.__version__)
  log.warning("[SKIP] pyarrow not available under Python 3.15 beta")
  log.error("[FAIL] import failed: %s", exc)
  log.critical("Fatal — cannot continue without virtual environment")

DEPENDENCIES
------------
  colorlog >= 6.0  (install: uv pip install colorlog)

NOTES
-----
  - The logs/ directory is created automatically relative to the project root,
    which is inferred as two levels above this file (scripts/../).
  - If colorlog is unavailable the module falls back to standard logging with
    no colors. A WARNING is emitted to notify the operator.
  - This module is intentionally dependency-light; it must import successfully
    even before the full data engineering stack is installed.
================================================================================
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root — resolved as the parent of the scripts/ directory.
# Adjust if the layout changes.
# ---------------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_LOGS_DIR: Path = _PROJECT_ROOT / "logs"

# ---------------------------------------------------------------------------
# Log format strings
# ---------------------------------------------------------------------------
_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d — %(message)s"
_FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# colorlog format — %(log_color)s injects the ANSI color for the level
_TERMINAL_FORMAT = (
    "%(log_color)s%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d%(reset)s"
    " — %(message)s"
)
_TERMINAL_DATE_FORMAT = "%H:%M:%S"  # Shorter for readability in the terminal

# Color mapping for each log level
_LOG_COLORS: dict[str, str] = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# ---------------------------------------------------------------------------
# Internal registry — avoids duplicate handlers when get_logger is called
# multiple times (e.g., in pytest sessions that import several scripts).
# ---------------------------------------------------------------------------
_configured_loggers: set[str] = set()


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Return a configured logger for *name*.

    Parameters
    ----------
    name:
        Typically ``__name__`` from the calling module.  Used as both the
        logger name and the stem of the rotating log file
        (``logs/<stem>.log``).
    level:
        Minimum log level for both handlers.  Defaults to DEBUG so that all
        messages are captured in the log file; the terminal handler uses the
        same level by default.

    Returns
    -------
    logging.Logger
        A logger with a colored StreamHandler and a RotatingFileHandler.
    """

    # Return early if already set up (prevents duplicate handlers on re-import)
    if name in _configured_loggers:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Do not bubble up to the root logger

    # ------------------------------------------------------------------
    # 1. Terminal handler — colored via colorlog
    # ------------------------------------------------------------------
    try:
        import colorlog  # noqa: PLC0415 — intentional late import

        terminal_handler = colorlog.StreamHandler(stream=sys.stdout)
        terminal_handler.setLevel(level)
        terminal_formatter = colorlog.ColoredFormatter(
            fmt=_TERMINAL_FORMAT,
            datefmt=_TERMINAL_DATE_FORMAT,
            log_colors=_LOG_COLORS,
            reset=True,
            style="%",
        )
        terminal_handler.setFormatter(terminal_formatter)

    except ImportError:
        # Graceful degradation — plain StreamHandler without colors.
        # This allows scripts to run before colorlog is installed (e.g.,
        # during validate_core.py's initial tool check).
        terminal_handler = logging.StreamHandler(stream=sys.stdout)
        terminal_handler.setLevel(level)
        plain_formatter = logging.Formatter(
            fmt=_FILE_FORMAT,
            datefmt=_FILE_DATE_FORMAT,
        )
        terminal_handler.setFormatter(plain_formatter)

        # Emit a visible warning so the operator knows colors are absent
        _tmp = logging.getLogger("logger.bootstrap")
        if not _tmp.handlers:
            _tmp.addHandler(terminal_handler)
        _tmp.warning(
            "colorlog not installed — terminal output will not be colored. "
            "Install with: uv pip install colorlog"
        )

    logger.addHandler(terminal_handler)

    # ------------------------------------------------------------------
    # 2. Rotating file handler
    # ------------------------------------------------------------------
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Derive a safe filename stem from the logger name.
    # e.g. "scripts.validate_stack" → "validate_stack"
    if name == "__main__":
        import sys as _sys
        from pathlib import Path as _Path
        main_path = getattr(_sys.modules.get("__main__"), "__file__", None)
        log_stem = _Path(main_path).stem if main_path else "__main__"
    else:
        log_stem = name.split(".")[-1] if "." in name else name
    log_path = _LOGS_DIR / f"{log_stem}.log"

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        mode="a",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        fmt=_FILE_FORMAT,
        datefmt=_FILE_DATE_FORMAT,
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # ------------------------------------------------------------------
    # Mark as configured and return
    # ------------------------------------------------------------------
    _configured_loggers.add(name)

    # Announce where logs are being written (INFO so it appears in green)
    logger.info("Logging initialized — file: %s", log_path)

    return logger


# ---------------------------------------------------------------------------
# Convenience re-exports so callers only need: from logger import get_logger
# ---------------------------------------------------------------------------
__all__ = ["get_logger"]
