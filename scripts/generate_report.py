#!/usr/bin/env python3
"""
===============================================================================
scripts/generate_report.py
===============================================================================
Project : Python 3.15 Data Engineering Validation Suite
Author  : Dr. Ceasar Jackson Jr.
Path    : scripts/generate_report.py

Purpose
-------
Support Python 3.15 data-engineering validation workflows.

Usage
-----
python scripts/generate_report.py

Validation
----------
python -m py_compile scripts/generate_report.py
python -m ruff check scripts/generate_report.py
python -m black --check scripts/generate_report.py

Exit Codes
----------
0   Success.
1   Failure or validation error.
130 User interrupted execution.

Operational Notes
-----------------
- Keep this script compatible with the active Python 3.15 validation environment.
- Prefer deterministic inputs and explicit validation commands.
- Preserve readable output suitable for terminal review and release notes.
- Keep this header intact for portfolio, audit, and future-maintainer reference.

===============================================================================


Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Generate Python 3.15 compatibility reports, manifests, summaries, and release artifacts.
    Validation: python -m py_compile scripts/generate_report.py; python scripts/generate_report.py --help
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
from contextlib import suppress
from datetime import date
from pathlib import Path

REPO = Path(__file__).parent.parent
REPORTS = REPO / "reports"
TEMPLATE = REPORTS / "template"

# Named logger. It has no handlers until main() calls _configure_logging(), so
# importing this module (tests, tools) never creates log files or writes output.
LOG = logging.getLogger("generate_report")


# Python each probe image must report. The check exists so a probe that passed
# on the wrong interpreter (for example the 3.14.x runtime in the old py314
# image) can never be recorded as evidence for 3.15. An image missing from this
# table is not version-checked. Keep in sync with scripts/validate_extended.py
# (tests/test_docker_pyspark_probe.py asserts the two tables are equal).
DOCKER_IMAGE_PYTHON = {
    "pyarrow-dataeng:py315": "3.15.1",
    "pyarrow-dataeng:py3152": "3.15.2",
}


def _configure_logging(file_logging=True):
    """Attach the shared colored console logger and, optionally, the file log.

    A dry run must write nothing, so main() passes file_logging=False for it and
    only the console sink is attached. The shared logger registers a name once per
    process, so the first call decides which sinks exist.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from logger import get_logger  # noqa: E402

    get_logger("generate_report", file_logging=file_logging)


def _log_result(label, status, detail=""):
    """Log one probe result at a severity that matches its status."""
    text = f"{label}: {status} ({detail})" if detail else f"{label}: {status}"
    if status == "PASS":
        LOG.info(text)
    elif status == "FAIL":
        LOG.error(text)
    else:
        # INCOMPAT, BLOCKED, SKIP and UNKNOWN are upstream or coverage gaps, not
        # faults in this tool, so they warn instead of erroring.
        LOG.warning(text)


def run(cmd, cwd=None, capture=True):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True,
        cwd=cwd or REPO,
        check=False,
    )
    stdout = result.stdout.strip() if result.stdout is not None else ""
    return stdout, result.returncode


def get_version(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"
    except FileNotFoundError:
        # Python 3.15 raises importlib.metadata.MetadataNotFound, which is a
        # FileNotFoundError and not a PackageNotFoundError, when a distribution
        # directory exists but has no metadata file (a broken install).
        return "metadata missing"


def run_validation_script(script):
    """Run a validation script and return (stdout, returncode)."""
    return run(f"{sys.executable} scripts/{script}")


def probe_package(pkg_name, test_fn=None):
    """Try to import a package and optionally run a quick test."""
    try:
        mod = __import__(pkg_name.replace("-", "_").replace(".", "_"))
        if test_fn:
            test_fn(mod)
        ver = get_version(pkg_name)
        return "PASS", ver
    except ImportError:
        return "FAIL", "not installed"
    except Exception as e:  # noqa: BLE001
        return "INCOMPAT", f"error: {e}"


def check_docker_image(image="pyarrow-dataeng:py314"):
    _, rc = run(f"docker image inspect {image}")
    return rc == 0


# Distribution names reported by `uv pip check` do not always match the keys
# used in the results dict (e.g. dist "apache-airflow" -> key "airflow").
_DIST_TO_RESULT_KEY = {
    "apache-airflow": "airflow",
    "dask": "dask.dataframe",
}


def _result_key_for_dist(dist_name, results):
    """Map a distribution name onto its key in the results dict."""
    if dist_name in results:
        return dist_name
    mapped = _DIST_TO_RESULT_KEY.get(dist_name)
    if mapped in results:
        return mapped
    # Fall back to a dotted key sharing the same root, e.g. "dask.dataframe".
    for key in results:
        if key.split(".")[0] == dist_name:
            return key
    return None


class DependencyCheck(list):
    """List-compatible violations with an explicit execution outcome."""

    def __init__(
        self,
        violations=(),
        *,
        status="UNKNOWN",
        returncode=None,
        stdout="",
        stderr="",
        error=None,
    ):
        super().__init__(violations)
        self.status = status
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error = error

    def as_dict(self):
        return {
            "status": self.status,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
        }


def _diagnostic_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def check_declared_support(results):
    """Downgrade packages that violate their own declared constraints.

    An import probe cannot detect a package that installs and imports cleanly
    while declaring the running interpreter unsupported (see PRE-001), nor an
    environment whose pins are mutually inconsistent (see ENV-002). Both show
    up in `uv pip check`, so its findings override probe results.

    Mutates ``results`` in place and returns list-compatible violations with diagnostics.
    """
    LOG.info("Verifying declared support constraints...")

    # `uv pip check` reports findings on stderr, not stdout, so the shared
    # run() helper (stdout only) cannot see them. Merge both streams here.
    try:
        proc = subprocess.run(
            ["uv", "pip", "check", "--python", sys.executable],
            capture_output=True,
            text=True,
            cwd=REPO,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        check = DependencyCheck(
            stdout=_diagnostic_text(getattr(exc, "stdout", "")),
            stderr=_diagnostic_text(getattr(exc, "stderr", "")),
            error=f"{type(exc).__name__}: {exc}",
        )
        _log_result("uv pip check", "UNKNOWN", check.error)
        return check

    output = f"{proc.stdout or ''}\n{proc.stderr or ''}".strip()
    violations = [
        line.strip()
        for line in output.splitlines()
        if re.match(r"The package `[^`]+` requires .+", line.strip())
    ]
    # uv uses exit 1 for detected incompatibilities. Other execution failures
    # are inconclusive unless a violation was actually reported.
    if violations or re.search(
        r"(?im)^Found [1-9]\d* incompatibilit(?:y|ies)\b", output
    ):
        status = "FAIL"
    elif proc.returncode == 0 and (
        not output
        or re.search(r"(?im)^All installed packages are compatible\.?$", output)
    ):
        status = "PASS"
    else:
        status = "UNKNOWN"
    check = DependencyCheck(
        violations,
        status=status,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )
    _log_result("uv pip check", status, f"exit {proc.returncode}")

    for line in violations:
        match = re.match(r"The package `([^`]+)` requires (.+)", line)
        if not match:
            continue
        dist, detail = match.group(1), match.group(2).rstrip(".")
        key = _result_key_for_dist(dist, results)

        if key is None:
            LOG.warning("%s: constraint violation (not tracked in report)", dist)
            continue

        previous = results[key].get("status")
        if previous in ("BLOCKED", "SKIP"):
            # Not installed or already excluded; nothing to downgrade.
            continue

        results[key] = {
            "status": "INCOMPAT",
            "version": results[key].get("version", get_version(dist)),
            "reason": f"declared unsupported: requires {detail}",
        }
        LOG.warning("%s: %s -> INCOMPAT (declared unsupported)", key, previous)

    return check


def _probe_prefect():
    """Classify Prefect at import level and return (result, console detail).

    This only imports ``flow`` and decorates a function; it never runs a flow, so a
    PASS here is import-level evidence, not Functional. Prefect's server code (where
    the 3.7.x beartype failure surfaced) loads later than ``import prefect``, so
    Functional evidence comes from the isolated-environment run
    (``validate_extended.py``) and ``reports/<release>/evidence.json``.

    Only a missing ``prefect`` module counts as "not installed". Any other import
    failure means Prefect is present but broken, which is an incompatibility and
    must not be hidden as a skip.
    """
    try:
        from prefect import flow

        @flow
        def _probe_flow():
            return "ok"

        version = get_version("prefect")
        return {"status": "PASS", "version": version}, version
    except ImportError as e:
        if "no_type_check_decorator" in str(e):
            return (
                {
                    "status": "INCOMPAT",
                    "version": get_version("prefect"),
                    "reason": "typing.no_type_check_decorator removed in Python 3.15",
                },
                "stdlib change",
            )
        if isinstance(e, ModuleNotFoundError) and e.name == "prefect":
            return {"status": "SKIP", "version": "not installed"}, "not installed"
        return (
            {
                "status": "INCOMPAT",
                "version": get_version("prefect"),
                "reason": f"prefect import failed: {e}",
            },
            f"import failed: {e}",
        )
    except Exception as e:  # noqa: BLE001
        return (
            {"status": "INCOMPAT", "version": get_version("prefect"), "reason": str(e)},
            str(e),
        )


def _is_absent(exc, *names):
    """True only when one of the named modules itself is missing.

    A ModuleNotFoundError for some other module means the package is installed
    but a dependency is broken, which is an incompatibility, not a skip.
    """
    return isinstance(exc, ModuleNotFoundError) and exc.name in names


def _probe_pyarrow():
    """Classify pyarrow; absence means no cp315 wheel, anything else is a break."""
    try:
        import pyarrow as pa

        return {"status": "PASS", "version": pa.__version__}, pa.__version__
    except ImportError as e:
        if _is_absent(e, "pyarrow"):
            return (
                {
                    "status": "BLOCKED",
                    "version": "unavailable",
                    "reason": "no cp315 wheels on PyPI; source build fails at CMake config",
                },
                "no cp315 wheels",
            )
        return (
            {
                "status": "INCOMPAT",
                "version": get_version("pyarrow"),
                "reason": f"pyarrow import failed: {e}",
            },
            f"import failed: {e}",
        )


def _probe_dask():
    """Classify dask.dataframe; its known failure is the runtime pyarrow dependency."""
    try:
        import dask.dataframe  # noqa: F401

        return {"status": "PASS", "version": get_version("dask")}, ""
    except ImportError as e:
        if "pyarrow" in str(e):
            return (
                {
                    "status": "INCOMPAT",
                    "version": get_version("dask"),
                    "reason": "runtime pyarrow dep",
                },
                "pyarrow dep",
            )
        if _is_absent(e, "dask", "dask.dataframe"):
            return {"status": "SKIP", "version": "not installed"}, ""
        return (
            {
                "status": "INCOMPAT",
                "version": get_version("dask"),
                "reason": f"dask.dataframe import failed: {e}",
            },
            f"import failed: {e}",
        )


def _probe_mlflow():
    """Classify mlflow; pyarrow (hard dependency since 2.17) is the known blocker."""
    try:
        import mlflow  # noqa: F401

        return {"status": "PASS", "version": get_version("mlflow")}, ""
    except Exception as e:  # noqa: BLE001
        if "pyarrow" in str(e).lower() or "opentelemetry" in str(e).lower():
            return (
                {
                    "status": "INCOMPAT",
                    "version": get_version("mlflow"),
                    "reason": "pyarrow hard dep",
                },
                "pyarrow dep",
            )
        if _is_absent(e, "mlflow"):
            return {"status": "SKIP", "version": "not installed"}, ""
        return (
            {
                "status": "INCOMPAT",
                "version": get_version("mlflow"),
                "reason": f"mlflow import failed: {e}",
            },
            f"import failed: {e}",
        )


def _probe_ray():
    """Classify ray; absence means no cp315 wheel, anything else is a break."""
    try:
        import ray  # noqa: F401

        return {"status": "PASS", "version": get_version("ray")}, ""
    except ImportError as e:
        if _is_absent(e, "ray"):
            return (
                {
                    "status": "BLOCKED",
                    "version": "unavailable",
                    "reason": "no cp315 wheels on PyPI",
                },
                "no cp315 wheels",
            )
        return (
            {
                "status": "INCOMPAT",
                "version": get_version("ray"),
                "reason": f"ray import failed: {e}",
            },
            f"import failed: {e}",
        )


def collect_results(docker_image="pyarrow-dataeng:py314"):
    """Run quick import probes for all tracked packages."""
    LOG.info("Probing core stack...")

    results = {}

    # Core packages
    for pkg in [
        "numpy",
        "pandas",
        "polars",
        "duckdb",
        "sqlalchemy",
        "pydantic",
        "matplotlib",
        "plotly",
        "jupyterlab",
    ]:
        status, ver = probe_package(pkg)
        results[pkg] = {"status": status, "version": ver}
        _log_result(pkg, status, ver)

    # sqlite3 — stdlib
    try:
        import sqlite3

        results["sqlite3"] = {"status": "PASS", "version": sqlite3.sqlite_version}
        _log_result("sqlite3", "PASS", sqlite3.sqlite_version)
    except Exception:  # noqa: BLE001
        results["sqlite3"] = {"status": "FAIL", "version": "stdlib"}
        _log_result("sqlite3", "FAIL", "stdlib import failed")

    # Extended stack. Order matters: it is the key order of the manifest.
    LOG.info("Probing extended stack...")
    for key, probe in (
        ("pyarrow", _probe_pyarrow),
        ("dask.dataframe", _probe_dask),
        ("prefect", _probe_prefect),
        ("mlflow", _probe_mlflow),
        ("ray", _probe_ray),
    ):
        results[key], detail = probe()
        _log_result(key, results[key]["status"], detail)

    # pyspark via docker — uses file mount to avoid stdin hang
    if check_docker_image(docker_image):
        LOG.info("Testing PySpark via Docker...")
        import os as _os
        import tempfile

        _spark_script = (
            "import json, sys, pyspark\n"
            "from pyspark.sql import SparkSession\n"
            "spark = SparkSession.builder.master('local[1]')"
            ".appName('report').config('spark.ui.enabled','false')"
            ".config('spark.driver.memory','512m').getOrCreate()\n"
            "spark.sparkContext.setLogLevel('ERROR')\n"
            "df = spark.createDataFrame([(1,'ok')],['id','s'])\n"
            "assert df.count()==1\n"
            "spark.stop()\n"
            "print(json.dumps({'status':'pass','version':pyspark.__version__,"
            "'python':sys.version.split()[0]}))\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".py",
            delete=False,
            prefix="spark_probe_",
        ) as _f:
            _f.write(_spark_script)
            _tmp = _f.name
        try:
            import subprocess as _sp

            _r = _sp.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{_tmp}:/tmp/spark_probe.py:ro",
                    docker_image,
                    "python3",
                    "/tmp/spark_probe.py",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            out, rc = _r.stdout, _r.returncode
        except _sp.TimeoutExpired:
            out, rc = "", 1
        finally:
            _os.unlink(_tmp)
        try:
            payload = json.loads(
                [line for line in out.splitlines() if line.strip()][-1]
            )
            expected_python = DOCKER_IMAGE_PYTHON.get(docker_image)
            version_matches = (
                expected_python is None or payload.get("python") == expected_python
            )
            if rc == 0 and payload.get("status") == "pass" and version_matches:
                results["pyspark"] = {
                    "status": "PASS",
                    "version": payload["version"],
                    # Record the container's own interpreter and image: the
                    # host Python says nothing about what ran inside Docker.
                    "note": (
                        f"via Docker image {docker_image} "
                        f"(Python {payload.get('python', 'unknown')}) + OpenJDK 21"
                    ),
                }
                _log_result(
                    "pyspark",
                    "PASS",
                    f"{payload['version']} via Docker (Python "
                    f"{payload.get('python', 'unknown')})",
                )
            else:
                # Say WHY: a probe that passed on the wrong interpreter must not
                # read as a generic failure.
                if rc == 0 and payload.get("status") == "pass":
                    reason = (
                        f"Docker image {docker_image} ran Python "
                        f"{payload.get('python', 'unknown')}, expected {expected_python}"
                    )
                else:
                    reason = "Docker test failed"
                results["pyspark"] = {
                    "status": "FAIL",
                    "version": "unknown",
                    "reason": reason,
                }
                _log_result("pyspark", "FAIL", reason)
        except Exception:  # noqa: BLE001
            results["pyspark"] = {
                "status": "INCOMPAT",
                "version": "unknown",
                "reason": "Docker test error",
            }
            _log_result("pyspark", "INCOMPAT")
    else:
        results["pyspark"] = {
            "status": "SKIP",
            "version": "unknown",
            "reason": "Docker image not available",
        }
        _log_result("pyspark", "SKIP", "Docker image not found")

    # apache-airflow
    try:
        from datetime import datetime as _dt

        import airflow as _af
        from airflow.providers.standard.operators.python import PythonOperator as _PO
        from airflow.sdk import DAG as _DAG

        _dag = _DAG("probe", start_date=_dt(2026, 1, 1), schedule=None)
        _PO(task_id="t", python_callable=lambda: None, dag=_dag)
        results["apache-airflow"] = {
            "status": "PASS",
            "version": _af.__version__,
            "note": "DAG + PythonOperator; operators moved to providers.standard in 3.x",
        }
        _log_result("airflow", "PASS", _af.__version__)
    except ImportError:
        results["apache-airflow"] = {
            "status": "SKIP",
            "version": "not installed",
            "reason": "not installed",
        }
        _log_result("airflow", "SKIP", "not installed")
    except Exception as e:  # noqa: BLE001
        results["apache-airflow"] = {
            "status": "INCOMPAT",
            "version": "unknown",
            "reason": str(e),
        }
        _log_result("airflow", "INCOMPAT", str(e))

    return results


def detect_python_build():
    """Identify the interpreter that is actually running.

    This must never be derived from the ``--release`` argument. A report whose
    build string is synthesised from the requested release will happily claim
    ``cpython-3.15.0rc1-...`` while running on b4 — which is exactly how the
    2026-08-05 rc1 report came to contradict its own ``python_runtime`` field.
    """
    # uv-managed interpreters live in a directory whose name IS the build
    # triple (e.g. cpython-3.15.0b4-macos-aarch64-none). That is ground truth,
    # so prefer it. sys._base_executable points at the real interpreter rather
    # than the venv shim.
    base = Path(getattr(sys, "_base_executable", None) or sys.executable).resolve()
    for part in base.parts:
        if part.startswith("cpython-"):
            return part

    # Otherwise synthesise an equivalent triple from the live interpreter.
    os_name = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(
        platform.system(), platform.system().lower()
    )
    return (
        f"{sys.implementation.name}-{platform.python_version()}"
        f"-{os_name}-{platform.machine()}-none"
    )


def verify_release_matches_runtime(release, allow_mismatch=False):
    """Refuse to label a report with a release the interpreter is not running.

    `uv python install 3.15` resolves to the newest build uv knows about, which
    lags upstream by days around a release. Combined with `uv venv` declining to
    replace an existing venv, a full validation cycle can re-measure the *old*
    environment and file the result under the new release name. Catch that here
    rather than discovering it later in the manifest.
    """
    runtime = platform.python_version()
    if runtime == release:
        return

    banner = (
        f"\n  Requested release : {release}"
        f"\n  Running interpreter: {runtime}"
        f"\n  Interpreter path   : {sys.executable}"
    )
    if allow_mismatch:
        LOG.warning("Interpreter does not match --release.%s", banner)
        LOG.warning("Continuing because --allow-version-mismatch was passed.")
        LOG.warning("The resulting report is NOT a validation of %s.", release)
        return

    LOG.error("Interpreter does not match --release.%s", banner)
    LOG.error(
        "\n  Refusing to write a report labelled with a release that was not"
        "\n  exercised. To fix:"
        f"\n      uv python install {release}"
        f"\n      uv venv --clear --python {release}"
        "\n      uv pip install -r requirements-py315-build.txt"
        "\n      uv pip install -r requirements-py315-dataeng-jupyter.txt"
        "\n"
        "\n  Note the --clear flag: without it uv leaves the existing venv in"
        "\n  place and the whole cycle silently re-measures the old build."
        "\n"
        "\n  Pass --allow-version-mismatch to override deliberately.\n"
    )
    sys.exit(1)


def tally(results):
    counts = {"PASS": 0, "FAIL": 0, "INCOMPAT": 0, "SKIP": 0, "BLOCKED": 0}
    for v in results.values():
        s = v["status"]
        counts[s] = counts.get(s, 0) + 1
    return counts


def write_manifest(
    release_dir,
    release,
    results,
    counts,
    docker_image="pyarrow-dataeng:py314",
    violations=None,
):
    # An old-style empty list does not prove that a check ran successfully.
    dependency_check = (
        violations
        if isinstance(violations, DependencyCheck)
        else DependencyCheck(
            violations or (), status="FAIL" if violations else "UNKNOWN"
        )
    )
    status = dependency_check.status
    if dependency_check:
        status = "FAIL"
    elif status != "FAIL" and (
        status != "PASS" or dependency_check.returncode != 0 or dependency_check.error
    ):
        status = "UNKNOWN"
    diagnostics = dependency_check.as_dict()
    diagnostics["status"] = status
    py_ver = platform.python_version()
    manifest = {
        "project": "Python 3.15 Data Engineering Validation Suite",
        "release": release,
        "release_type": "beta" if "b" in release else "rc" if "rc" in release else "ga",
        "test_date": date.today().isoformat(),
        "platform": f"macOS {platform.mac_ver()[0]} ARM64",
        "python_build": detect_python_build(),
        "python_runtime": py_ver,
        "package_manager": "uv",
        "docker_image": docker_image,
        "tester": "Dr. Ceasar Jackson Jr.",
        "suite_version": "1.2.0",
        "packages_tested": sum(counts.values()),
        "packages_pass": counts["PASS"],
        "packages_incompat": counts["INCOMPAT"],
        "packages_blocked": counts["BLOCKED"],
        "packages_skip": counts["SKIP"],
        "packages_fail": counts["FAIL"],
        # Recorded so a report can be audited for environment integrity,
        # not just import success. See ENV-002 and PRE-001.
        "environment_consistent": (
            True if status == "PASS" else False if status == "FAIL" else None
        ),
        "dependency_check": diagnostics,
        "constraint_violations": list(violations or []),
        "results": results,
    }
    # Keep report generation aligned with tools/sync_readiness.py.
    # SKIP entries are excluded from the denominator; BLOCKED and INCOMPAT
    # receive partial credit because they represent upstream/support gaps
    # rather than direct runtime failures.
    _eff = sum(counts.values()) - counts.get("SKIP", 0)
    _wp = (
        counts["PASS"]
        + counts.get("BLOCKED", 0) * 0.50
        + counts.get("INCOMPAT", 0) * 0.25
    )
    manifest["production_readiness_pct"] = (
        min(round((_wp / _eff) * 100), 100) if _eff else 0
    )
    # Defensive schema guarantee for downstream tests.
    manifest.setdefault("packages_blocked", counts.get("BLOCKED", 0))

    # print("\nDEBUG BEFORE WRITE")
    # print("packages_blocked =", manifest.get("packages_blocked"))
    # print(sorted(manifest.keys()))

    manifest_path = release_dir / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, indent=2))

    # written = json.loads(manifest_path.read_text(encoding="utf-8"))
    # print("\nDEBUG AFTER WRITE")
    # print("packages_blocked =", written.get("packages_blocked"))
    # print(sorted(written.keys()))


def write_compat_report(release_dir, release, results, counts):
    def badge(status):
        return {
            "PASS": "✅ PASS",
            "FAIL": "❌ FAIL",
            "INCOMPAT": "⚠️ INCOMPAT",
            "BLOCKED": "🚫 BLOCKED",
            "SKIP": "⏭️ SKIP",
        }.get(status, status)

    core = [
        "numpy",
        "pandas",
        "polars",
        "duckdb",
        "sqlalchemy",
        "pydantic",
        "matplotlib",
        "plotly",
        "jupyterlab",
        "sqlite3",
    ]
    extended = [
        "pyspark",
        "dask.dataframe",
        "pyarrow",
        "mlflow",
        "prefect",
        "ray",
        "apache-airflow",
    ]

    lines = [
        f"# Compatibility Report \u2014 Python {release}",
        "",
        f"**Date:** {date.today().strftime('%B %d, %Y')}",
        f"**Platform:** macOS {platform.mac_ver()[0]} {platform.machine()}",
        "**Tester:** Dr. Ceasar Jackson Jr.",
        "**Suite Version:** 1.2.0",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Packages Tested | {sum(counts.values())} |",
        f"| PASS | {counts['PASS']} |",
        f"| INCOMPAT | {counts['INCOMPAT']} |",
        f"| BLOCKED | {counts.get('BLOCKED', 0)} |",
        f"| SKIP | {counts['SKIP']} |",
        f"| FAIL | {counts['FAIL']} |",
        "",
        "---",
        "",
        "## Core Stack",
        "",
        "| Package | Version | Result | Notes |",
        "|---------|---------|--------|-------|",
    ]
    for pkg in core:
        r = results.get(pkg, {"status": "SKIP", "version": "—"})
        note = r.get("reason", r.get("note", ""))
        lines.append(f"| {pkg} | {r['version']} | {badge(r['status'])} | {note} |")

    lines += [
        "",
        "## Extended Stack",
        "",
        "| Package | Version | Result | Notes |",
        "|---------|---------|--------|-------|",
    ]
    for pkg in extended:
        r = results.get(pkg, {"status": "SKIP", "version": "—"})
        note = r.get("reason", r.get("note", ""))
        lines.append(f"| {pkg} | {r['version']} | {badge(r['status'])} | {note} |")

    lines += [
        "",
        "---",
        "",
        "## Changes from Previous Cycle",
        "",
        "*Compare with previous report using:*",
        "```bash",
        f"python scripts/compare_reports.py <previous> {release}",
        "```",
        "",
        "---",
        "",
        f"*Generated {date.today().isoformat()} by "
        f"Python 3.15 Data Engineering Validation Suite v1.2.0*",
    ]

    with (release_dir / "compatibility_report.md").open(
        "x", encoding="utf-8"
    ) as handle:
        handle.write("\n".join(lines))


SCAFFOLD_FILES = frozenset(
    {
        "RELEASE_CHECKLIST.md",
        "readiness_matrix.md",
        "executive_summary.md",
        "full_readiness_assessment.md",
    }
)


def is_scaffold_only_directory(release_dir):
    """Recognize exactly four regular scaffold files, without symlinks."""
    if release_dir.is_symlink() or not release_dir.is_dir():
        return False
    entries = list(release_dir.iterdir())
    return {entry.name for entry in entries} == SCAFFOLD_FILES and all(
        entry.is_file() and not entry.is_symlink() for entry in entries
    )


def publish_artifacts(staging_dir, release_dir):
    """Publish exclusively into a new or verified scaffold-only directory.

    Hard links expose complete files; the manifest is published last.
    On failure, remove only links created by this attempt.
    """
    created_directory = False
    try:
        release_dir.mkdir(exist_ok=False)
        created_directory = True
    except FileExistsError:
        if not is_scaffold_only_directory(release_dir):
            raise

    published = []
    try:
        for name in ("compatibility_report.md", "manifest.json"):
            source = staging_dir / name
            target = release_dir / name
            os.link(source, target)
            published.append((source, target))
    except BaseException:
        for source, target in reversed(published):
            if target.exists() and target.samefile(source):
                target.unlink()
        if created_directory:
            # Remove only a newly created, empty directory.
            with suppress(OSError):
                release_dir.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Generate a versioned compatibility report"
    )
    parser.add_argument(
        "--release", required=True, help="Python release, e.g. 3.15.0rc1"
    )
    parser.add_argument(
        "--auto-commit", action="store_true", help="Git commit after generating"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results without writing"
    )
    parser.add_argument(
        "--allow-version-mismatch",
        action="store_true",
        help=(
            "Generate the report even when the running interpreter is not the "
            "release named by --release. The result is not a validation of "
            "that release; use only deliberately."
        ),
    )
    parser.add_argument(
        "--docker-image",
        default=os.environ.get("DATAENG_DOCKER_IMAGE", "pyarrow-dataeng:py314"),
        help=(
            "Docker image for PySpark/PyArrow isolation "
            "(default: pyarrow-dataeng:py314, or DATAENG_DOCKER_IMAGE env var)"
        ),
    )
    args = parser.parse_args()

    release = args.release
    if not re.fullmatch(r"3\.15\.\d+(?:(?:a|b|rc)\d+)?", release):
        parser.error("--release must be a Python 3.15 release identifier")
    release_dir = REPORTS / release

    # A dry run must not create a log file, so it gets the console sink only.
    _configure_logging(file_logging=not args.dry_run)

    if args.dry_run:
        LOG.info(
            f"Dry run: would verify runtime {release}, probe packages and dependencies,"
        )
        LOG.info(
            f"stage manifest.json and compatibility_report.md, then publish to {release_dir}."
        )
        LOG.info(
            "Existing destinations would be refused. No probes run or files written."
        )
        if args.auto_commit:
            LOG.info("Would stage and commit the generated report (--auto-commit).")
        return

    if os.path.lexists(release_dir) and not is_scaffold_only_directory(release_dir):
        parser.error(f"Refusing to overwrite existing report: {release_dir}")
    verify_release_matches_runtime(release, args.allow_version_mismatch)

    LOG.info("Generating compatibility report for Python %s", release)
    LOG.info("Output: %s", release_dir)
    LOG.info("=" * 60)

    results = collect_results(docker_image=args.docker_image)
    violations = check_declared_support(results)
    counts = tally(results)
    LOG.info(
        f"Results: PASS={counts['PASS']}  FAIL={counts['FAIL']}  "
        f"INCOMPAT={counts['INCOMPAT']}  BLOCKED={counts.get('BLOCKED', 0)}  "
        f"SKIP={counts['SKIP']}"
    )
    _log_result("Dependency check", violations.status)

    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".report-stage-", dir=REPORTS) as staging:
        staging_dir = Path(staging)
        write_manifest(
            staging_dir,
            release,
            results,
            counts,
            docker_image=args.docker_image,
            violations=violations,
        )
        write_compat_report(staging_dir, release, results, counts)
        publish_artifacts(staging_dir, release_dir)

    LOG.info("Report written to reports/%s/", release)
    for f in sorted(release_dir.iterdir()):
        LOG.info("  %s  (%s bytes)", f.name, f"{f.stat().st_size:,}")

    if args.auto_commit:
        run(f"git add reports/{release}/", capture=False)
        run(
            f'git commit -m "report: add {release} compatibility report"', capture=False
        )
        LOG.info("Committed: report: add %s compatibility report", release)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # 130 = 128 + SIGINT, the shell convention for "stopped by Ctrl-C".
        # Exit quietly instead of dumping a traceback over the user's terminal.
        sys.stderr.write("\nInterrupted by user.\n")
        raise SystemExit(130) from None
