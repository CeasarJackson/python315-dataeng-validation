#!/usr/bin/env python3
"""
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
File    : scripts/check_cp315_wheels.py

Purpose
-------
Answer one question without needing a Python 3.15 interpreter installed:
for a given package, has upstream published a binary wheel that a cp315
runtime on macOS ARM64 can actually install?

The June 2026 readiness assessment identified absent cp315 wheels as the
single upstream gate holding back PyArrow and everything that depends on it.
Re-checking that gate by hand is slow and error-prone, so this script drives
``pip download`` in resolve-only mode against an explicit target platform and
reports what came back.

The critical subtlety this script exists to handle: ``pip download --abi
cp315`` does NOT restrict results to cp315-tagged wheels. Pip will happily
satisfy the request with a ``py3-none-any`` pure-Python wheel or a
``cpXX-abi3`` stable-ABI wheel, both of which are legitimately installable on
3.15. Reading only pip's exit status therefore produces false positives — a
pure-Python package looks like it "has a cp315 wheel" when it has no compiled
artifact at all. We parse the returned filename and classify it into one of
four kinds so the distinction survives into the report:

    native   cp315-cp315-<platform>   purpose-built for 3.15, the real signal
    abi3     cpXX-abi3-<platform>     stable ABI, forward-compatible, fine
    pure     py3-none-any             no compiled code, platform-irrelevant
    none     nothing resolved         genuinely blocked

Only ``none`` is a blocker. Only ``native`` proves upstream has cut 3.15
builds. Conflating the middle two is what makes casual wheel checks wrong.

Security
--------
This script touches no credentials. It performs unauthenticated reads against
the configured package index only, and writes nothing outside the temporary
download directory and the project log file.

Usage
-----
    python scripts/check_cp315_wheels.py
    python scripts/check_cp315_wheels.py --packages pyarrow ray duckdb
    python scripts/check_cp315_wheels.py --python-version 3.16 --abi cp316
    python scripts/check_cp315_wheels.py --platforms manylinux_2_28_aarch64
    python scripts/check_cp315_wheels.py --json results.json

Exit Codes
----------
0   Every requested package resolved to some installable wheel.
1   At least one package has no installable wheel for the target.
2   Invalid command-line usage.
130 User interrupted execution.

Log files
---------
    logs/check_cp315_wheels.log
===============================================================================


Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Classify upstream wheel availability for a cp315 target without
        requiring a Python 3.15 interpreter to be installed.
    Validation: python -m py_compile scripts/check_cp315_wheels.py; python scripts/check_cp315_wheels.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap path — mirrors the pattern used by validate_extended.py so the
# script runs correctly whether invoked as `python scripts/check_cp315_wheels.py`
# or imported by the pytest suite.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Result classification
# ---------------------------------------------------------------------------
NATIVE = "native"  # cp315-cp315 — upstream cut a 3.15-specific build
ABI3 = "abi3"  # stable ABI — installable on 3.15, built against an older cp
PURE = "pure"  # py3-none-any — no compiled extension at all
NONE = "none"  # nothing resolved — this is the blocker state

# The June assessment's blocker set, plus the core stack it depends on. Kept
# here rather than in a config file so the script is self-contained when
# copied to a machine that only has the scripts/ directory.
DEFAULT_PACKAGES = [
    # Core stack — expected PASS in the June baseline
    "numpy",
    "pandas",
    "polars",
    "duckdb",
    "sqlalchemy",
    "pydantic",
    "matplotlib",
    "plotly",
    "jupyterlab",
    # Blocked in June — the packages this script exists to watch
    "pyarrow",
    "ray",
    "deltalake",
    "dask",
    "mlflow",
    "prefect",
    "apache-airflow",
    "pyspark",
]

# macOS ARM64 deployment targets, oldest first. Pip matches --platform against
# wheel tags by exact string, with no compatibility expansion, so a single
# guess produces false negatives: NumPy tags macosx_11_0_arm64 while SciPy
# tags macosx_12_0_arm64. We sweep the plausible range and take the first hit.
DEFAULT_PLATFORMS = [
    "macosx_11_0_arm64",
    "macosx_12_0_arm64",
    "macosx_13_0_arm64",
    "macosx_14_0_arm64",
    "macosx_15_0_arm64",
    "macosx_26_0_arm64",
]

_WHEEL_RE = re.compile(r"[A-Za-z0-9_.+-]+\.whl")


@dataclass
class ProbeResult:
    """Outcome of probing one package against one target."""

    package: str
    kind: str
    wheel: str | None
    platform: str | None

    @property
    def blocked(self) -> bool:
        return self.kind == NONE


def _classify(wheel_name: str, abi: str) -> str:
    """Classify *wheel_name* by its ABI tag.

    Wheel filenames are ``name-version(-build)?-python-abi-platform.whl``. We
    read the ABI segment rather than the Python segment because that is what
    determines runtime installability: a ``cp311-abi3`` wheel loads fine on
    3.15, whereas ``cp311-cp311`` does not.
    """
    stem = wheel_name.removesuffix(".whl")
    parts = stem.split("-")
    if len(parts) < 3:
        return PURE
    abi_tag = parts[-2]

    if abi_tag == abi:
        return NATIVE
    if abi_tag == "abi3":
        return ABI3
    if abi_tag == "none":
        return PURE
    # Some other cp tag satisfied the resolve. Treat as pure/unknown rather
    # than native so we never overstate 3.15 readiness.
    return PURE


def _probe_one(
    package: str,
    platform: str,
    python_version: str,
    abi: str,
    dest: Path,
) -> str | None:
    """Return the resolved wheel filename for one platform, or None.

    ``--no-deps`` keeps this a single-package question; resolving the full
    dependency tree would fail for unrelated reasons and muddy the signal.
    """
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--no-deps",
        "--only-binary=:all:",
        "--python-version",
        python_version,
        "--implementation",
        "cp",
        "--abi",
        abi,
        "--platform",
        platform,
        "--dest",
        str(dest),
        package,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
    except subprocess.TimeoutExpired:
        log.warning("[WARN] %s — pip timed out on %s", package, platform)
        return None

    if proc.returncode != 0:
        return None

    match = _WHEEL_RE.search(proc.stdout)
    return match.group(0) if match else None


def probe(
    package: str,
    platforms: list[str],
    python_version: str,
    abi: str,
) -> ProbeResult:
    """Probe *package* across *platforms*, returning the first resolution."""
    # Each probe gets a clean temp directory. Reusing one lets pip report
    # "File was already downloaded" for a *previous* package's wheel, which
    # silently corrupts the filename parse.
    dest = Path(tempfile.mkdtemp(prefix=f"whlprobe_{package}_"))
    try:
        for platform in platforms:
            wheel = _probe_one(package, platform, python_version, abi, dest)
            if wheel:
                kind = _classify(wheel, abi)
                return ProbeResult(package, kind, wheel, platform)
        return ProbeResult(package, NONE, None, None)
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def _report(result: ProbeResult) -> None:
    """Emit one classified result at the severity its meaning deserves."""
    if result.kind == NATIVE:
        log.info("[PASS] %-16s native %s wheel — %s", result.package, "cp315", result.wheel)
    elif result.kind == ABI3:
        log.info(
            "[PASS] %-16s stable-ABI wheel, installable on target — %s",
            result.package,
            result.wheel,
        )
    elif result.kind == PURE:
        log.info(
            "[PASS] %-16s pure-Python wheel, no compiled extension — %s",
            result.package,
            result.wheel,
        )
    else:
        log.error(
            "[FAIL] %-16s no installable wheel for the requested target — BLOCKED",
            result.package,
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether upstream has published wheels installable on a "
            "target CPython ABI, without needing that interpreter locally."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--packages",
        nargs="+",
        default=DEFAULT_PACKAGES,
        help="Packages to probe. Defaults to the readiness-assessment set.",
    )
    parser.add_argument(
        "--python-version",
        default="3.15",
        help="Target Python version passed to pip. Default: 3.15",
    )
    parser.add_argument(
        "--abi",
        default="cp315",
        help="Target ABI tag treated as 'native'. Default: cp315",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=DEFAULT_PLATFORMS,
        help="Platform tags to sweep, first hit wins. Default: macOS ARM64 11-26.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Also write structured results to this path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    log.info("Target: Python %s / ABI %s", args.python_version, args.abi)
    log.info("Platform sweep: %s", ", ".join(args.platforms))
    log.info("Probing %d package(s)", len(args.packages))

    results: list[ProbeResult] = []
    for package in args.packages:
        result = probe(package, args.platforms, args.python_version, args.abi)
        _report(result)
        results.append(result)

    blocked = [r.package for r in results if r.blocked]
    native = [r.package for r in results if r.kind == NATIVE]

    log.info("-" * 70)
    log.info(
        "Summary: %d probed | %d native %s | %d blocked",
        len(results),
        len(native),
        args.abi,
        len(blocked),
    )
    if blocked:
        log.error("Blocked: %s", ", ".join(blocked))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([asdict(r) for r in results], indent=2))
        log.info("Structured results written to %s", args.json)

    return 1 if blocked else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        raise SystemExit(130) from None
