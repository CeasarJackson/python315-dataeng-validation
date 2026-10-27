#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : scripts/profile_with_tachyon.py

Purpose
-------
Run one of the benchmark scripts under Tachyon, the statistical sampling
profiler that ships with Python 3.15 as ``profiling.sampling`` (PEP 799), and
keep the profile next to the other generated outputs.

Tachyon has no Python API. It is driven only through
``python -m profiling.sampling run ...``, so the benchmark scripts cannot call
it from inside themselves. This wrapper is the supported way to do it: the
benchmark files stay unchanged, so their timing numbers are never affected by
profiling code. The profiler samples from a separate process, which is also why
profiled timings must not be compared with the unprofiled benchmark numbers.

Compatibility decisions
-----------------------
* Tachyon exists only on 3.15+. On older interpreters the script stops with
  exit code 3 and a message, instead of failing on an ImportError.
* The profiler and the target run under the same interpreter (the one running
  this script), because Tachyon requires matching minor versions.
* On macOS, Tachyon reads the target's memory. ``run`` may need elevated
  permission (root, or the debugger entitlement). If the profiler fails with a
  permission-looking message the script says so and does not retry with sudo.
  That choice is yours.

Security
--------
No credentials are used. The target script and its arguments are passed to the
profiler as an argv list, never through a shell. Output is written only under
the chosen output directory and never over an existing file.

Usage
-----
    python scripts/profile_with_tachyon.py
    python scripts/profile_with_tachyon.py --dry-run
    python scripts/profile_with_tachyon.py --format pstats --rate 5khz
    python scripts/profile_with_tachyon.py --target scripts/benchmark_duckdb_pyarrow.py
    python scripts/profile_with_tachyon.py -- --help     # args after -- go to the target

Examples
--------
    .venv3151/bin/python scripts/profile_with_tachyon.py --format flamegraph
    -> outputs/profiles/benchmark_pandas_polars_20261026_213000.html

Exit Codes
----------
0   Profile written and verified.
1   The profiler or the target failed, or no profile file was produced.
2   Invalid command-line usage (missing target, bad rate, unwritable output).
3   Tachyon is unavailable (Python older than 3.15, or the module is missing).
130 User interrupted execution.

Log files
---------
    logs/profile_with_tachyon.log
===============================================================================


Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Run a benchmark under Python 3.15's Tachyon sampling profiler.
    Validation: python -m py_compile scripts/profile_with_tachyon.py; python scripts/profile_with_tachyon.py --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap path, same pattern as the other scripts in this directory.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "scripts" / "benchmark_pandas_polars.py"
# outputs/ is already gitignored, so profiles are never committed by accident.
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiles"

# Output format -> (profiler flag, file extension). Every format is written with
# -o so the result is a file we can verify, never text on stdout.
FORMATS: dict[str, tuple[str, str]] = {
    "flamegraph": ("--flamegraph", ".html"),
    "pstats": ("--pstats", ".pstats"),
    "collapsed": ("--collapsed", ".collapsed"),
}

# Accepts "1000", "10k", "10khz" (case-insensitive), the forms Tachyon documents.
_RATE_RE = re.compile(r"^\d+(k|khz)?$", re.IGNORECASE)

# Substrings that suggest the OS refused the profiler access to the target.
_PERMISSION_HINTS = (
    "permission",
    "task_for_pid",
    "not permitted",
    "ptrace",
    "entitlement",
)


def tachyon_available() -> tuple[bool, str]:
    """Return (available, reason). The reason is empty when available."""
    if sys.version_info < (3, 15):
        return False, (
            f"Tachyon (profiling.sampling) needs Python 3.15 or newer; this is "
            f"{sys.version_info[0]}.{sys.version_info[1]}. "
            "Run the script with the 3.15 interpreter, for example .venv3151/bin/python."
        )
    try:
        found = importlib.util.find_spec("profiling.sampling") is not None
    except (ImportError, ValueError):
        found = False
    if not found:
        return False, "This Python 3.15 build has no profiling.sampling module."
    return True, ""


def build_output_path(target: Path, fmt: str, output_dir: Path, stamp: str) -> Path:
    """Timestamped output path, so repeated runs never collide."""
    return output_dir / f"{target.stem}_{stamp}{FORMATS[fmt][1]}"


def build_command(
    target: Path,
    fmt: str,
    rate: str,
    duration: int | None,
    output: Path,
    extra: list[str],
) -> list[str]:
    """Assemble the profiler command. Profiler options must precede the target."""
    cmd = [sys.executable, "-m", "profiling.sampling", "run", "-r", rate]
    if duration is not None:
        cmd += ["-d", str(duration)]
    cmd += [FORMATS[fmt][0], "-o", str(output), str(target), *extra]
    return cmd


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a benchmark under Python 3.15's Tachyon sampling profiler.",
        epilog="Arguments after -- are passed to the target script.",
    )
    parser.add_argument(
        "--target", type=Path, default=DEFAULT_TARGET, help="Script to profile."
    )
    parser.add_argument("--format", choices=sorted(FORMATS), default="flamegraph")
    parser.add_argument(
        "--rate", default="1khz", help="Sampling rate, e.g. 1000, 5k, 10khz."
    )
    parser.add_argument(
        "--duration", type=int, default=None, help="Stop profiling after N seconds."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--timeout", type=int, default=3600, help="Kill the run after N seconds."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show the command; run nothing."
    )
    args, extra = parser.parse_known_args(argv)
    # parse_known_args keeps a leading "--"; drop it so the target never sees it.
    args.extra = extra[1:] if extra[:1] == ["--"] else extra
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Validate inputs first, so a typo is reported even where Tachyon is absent.
    target = args.target if args.target.is_absolute() else PROJECT_ROOT / args.target
    if not target.is_file() or target.suffix != ".py":
        log.error("[FAIL] --target must be an existing .py file. Got %s", target)
        return 2
    if not _RATE_RE.match(args.rate):
        log.error("[FAIL] --rate must look like 1000, 5k or 10khz. Got %r", args.rate)
        return 2
    if args.duration is not None and args.duration <= 0:
        log.error(
            "[FAIL] --duration must be a positive number of seconds. Got %s",
            args.duration,
        )
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = build_output_path(target, args.format, args.output_dir, stamp)
    cmd = build_command(
        target, args.format, args.rate, args.duration, output, args.extra
    )

    if args.dry_run:
        # Dry run reports the plan even on interpreters without Tachyon, so the
        # command can be reviewed anywhere.
        log.info("Dry run: would run: %s", " ".join(cmd))
        log.info("Dry run: would write %s. Nothing was executed.", output)
        return 0

    available, reason = tachyon_available()
    if not available:
        log.error("[FAIL] %s", reason)
        return 3

    if output.exists():
        # Timestamped names make this unreachable in practice; refuse anyway
        # rather than ever overwrite an earlier profile.
        log.error("[FAIL] Refusing to overwrite existing profile %s", output)
        return 2
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        log.error("[FAIL] Cannot create output directory %s: %s", args.output_dir, exc)
        return 2

    log.info("Profiling %s with Tachyon (%s, %s)", target.name, args.format, args.rate)
    log.info("Command: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log.error(
            "[FAIL] Profiling run exceeded %d seconds and was stopped.", args.timeout
        )
        return 1
    except OSError as exc:
        log.error("[FAIL] Could not start the profiler: %s", exc)
        return 1

    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-8:])
        log.error("[FAIL] Profiler exited with code %d:\n%s", proc.returncode, tail)
        if any(hint in tail.lower() for hint in _PERMISSION_HINTS):
            log.warning(
                "[WARN] This looks like a permission problem. On macOS Tachyon needs "
                "root or the debugger entitlement; rerun deliberately with sudo if "
                "you want to proceed."
            )
        return 1

    # Post-run integrity check: the profiler can exit 0 yet write nothing.
    if not output.is_file() or output.stat().st_size == 0:
        log.error("[FAIL] Profiler exited cleanly but %s is missing or empty.", output)
        return 1

    log.info("[PASS] Profile written: %s (%d bytes)", output, output.stat().st_size)
    log.info(
        "Profiled timings include sampling overhead; do not compare them with benchmark CSVs."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        raise SystemExit(130) from None
