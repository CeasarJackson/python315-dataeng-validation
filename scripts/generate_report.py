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
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).parent.parent
REPORTS = REPO / "reports"
TEMPLATE = REPORTS / "template"


def run(cmd, cwd=None, capture=True):
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, cwd=cwd or REPO
    )
    stdout = result.stdout.strip() if result.stdout is not None else ""
    return stdout, result.returncode


def get_version(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


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
    except Exception as e:
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


def check_declared_support(results):
    """Downgrade packages that violate their own declared constraints.

    An import probe cannot detect a package that installs and imports cleanly
    while declaring the running interpreter unsupported (see PRE-001), nor an
    environment whose pins are mutually inconsistent (see ENV-002). Both show
    up in `uv pip check`, so its findings override probe results.

    Mutates ``results`` in place and returns the list of violation strings.
    """
    print("  Verifying declared support constraints...")

    # `uv pip check` reports findings on stderr, not stdout, so the shared
    # run() helper (stdout only) cannot see them. Merge both streams here.
    proc = subprocess.run(
        "uv pip check",
        shell=True,
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    output = f"{proc.stdout or ''}\n{proc.stderr or ''}".strip()
    rc = proc.returncode

    if rc == 0 and "Found" not in output:
        print("    uv pip check: no constraint violations")
        return []

    violations = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("The package ")
    ]

    if not violations:
        # Non-zero exit with no parsable detail — surface it rather than
        # silently treating the environment as clean.
        if rc != 0:
            print(f"    uv pip check: exited {rc}, output not parsable")
        return []

    for line in violations:
        match = re.match(r"The package `([^`]+)` requires (.+)", line)
        if not match:
            continue
        dist, detail = match.group(1), match.group(2).rstrip(".")
        key = _result_key_for_dist(dist, results)

        if key is None:
            print(f"    {dist}: constraint violation (not tracked in report)")
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
        print(f"    {key}: {previous} -> INCOMPAT (declared unsupported)")

    return violations


def collect_results(docker_image="pyarrow-dataeng:py314"):
    """Run quick import probes for all tracked packages."""
    print("  Probing core stack...")

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
        print(f"    {pkg}: {status} ({ver})")

    # sqlite3 — stdlib
    try:
        import sqlite3

        results["sqlite3"] = {"status": "PASS", "version": sqlite3.sqlite_version}
        print(f"    sqlite3: PASS ({sqlite3.sqlite_version})")
    except Exception:
        results["sqlite3"] = {"status": "FAIL", "version": "stdlib"}

    # pyarrow — known blocker
    print("  Probing extended stack...")
    try:
        import pyarrow as pa

        results["pyarrow"] = {"status": "PASS", "version": pa.__version__}
        print(f"    pyarrow: PASS ({pa.__version__})")
    except ImportError:
        results["pyarrow"] = {
            "status": "BLOCKED",
            "version": "unavailable",
            "reason": "no cp315 wheels on PyPI; source build fails at CMake config",
        }
        print("    pyarrow: BLOCKED (no cp315 wheels)")

    # dask
    try:
        import dask.dataframe  # noqa: F401

        results["dask.dataframe"] = {"status": "PASS", "version": get_version("dask")}
        print("    dask.dataframe: PASS")
    except ImportError as e:
        if "pyarrow" in str(e):
            results["dask.dataframe"] = {
                "status": "INCOMPAT",
                "version": get_version("dask"),
                "reason": "runtime pyarrow dep",
            }
            print("    dask.dataframe: INCOMPAT (pyarrow dep)")
        else:
            results["dask.dataframe"] = {"status": "SKIP", "version": "not installed"}
            print("    dask.dataframe: SKIP")

    # prefect — real import test (version heuristic was unreliable)
    try:
        from prefect import flow

        prefect_ver = get_version("prefect")

        @flow
        def _probe_flow():
            return "ok"

        results["prefect"] = {"status": "PASS", "version": prefect_ver}
        print(f"    prefect: PASS ({prefect_ver})")
    except ImportError as e:
        if "no_type_check_decorator" in str(e):
            results["prefect"] = {
                "status": "INCOMPAT",
                "version": get_version("prefect"),
                "reason": "typing.no_type_check_decorator removed in Python 3.15",
            }
            print("    prefect: INCOMPAT (stdlib change)")
        else:
            results["prefect"] = {"status": "SKIP", "version": "not installed"}
            print("    prefect: SKIP (not installed)")
    except Exception as e:
        results["prefect"] = {
            "status": "INCOMPAT",
            "version": get_version("prefect"),
            "reason": str(e),
        }
        print(f"    prefect: INCOMPAT ({e})")
    # mlflow
    try:
        import mlflow  # noqa: F401

        results["mlflow"] = {"status": "PASS", "version": get_version("mlflow")}
        print("    mlflow: PASS")
    except (ImportError, Exception) as e:
        if "pyarrow" in str(e).lower() or "opentelemetry" in str(e).lower():
            results["mlflow"] = {
                "status": "INCOMPAT",
                "version": get_version("mlflow"),
                "reason": "pyarrow hard dep",
            }
            print("    mlflow: INCOMPAT (pyarrow dep)")
        else:
            results["mlflow"] = {"status": "SKIP", "version": "not installed"}
            print("    mlflow: SKIP")

    # ray
    try:
        import ray  # noqa: F401

        results["ray"] = {"status": "PASS", "version": get_version("ray")}
        print("    ray: PASS")
    except ImportError:
        results["ray"] = {
            "status": "BLOCKED",
            "version": "unavailable",
            "reason": "no cp315 wheels on PyPI",
        }
        print("    ray: BLOCKED (no cp315 wheels)")

    # pyspark via docker — uses file mount to avoid stdin hang
    if check_docker_image(docker_image):
        print("  Testing PySpark via Docker...")
        import os as _os
        import tempfile

        _spark_script = (
            "import json, pyspark\n"
            "from pyspark.sql import SparkSession\n"
            "spark = SparkSession.builder.master('local[1]')"
            ".appName('report').config('spark.ui.enabled','false')"
            ".config('spark.driver.memory','512m').getOrCreate()\n"
            "spark.sparkContext.setLogLevel('ERROR')\n"
            "df = spark.createDataFrame([(1,'ok')],['id','s'])\n"
            "assert df.count()==1\n"
            "spark.stop()\n"
            "print(json.dumps({'status':'pass','version':pyspark.__version__}))\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="spark_probe_"
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
            if rc == 0 and payload.get("status") == "pass":
                results["pyspark"] = {
                    "status": "PASS",
                    "version": payload["version"],
                    "note": "via Docker py314 + OpenJDK 21",
                }
                print(f"    pyspark: PASS ({payload['version']} via Docker)")
            else:
                results["pyspark"] = {
                    "status": "FAIL",
                    "version": "unknown",
                    "reason": "Docker test failed",
                }
                print("    pyspark: FAIL")
        except Exception:
            results["pyspark"] = {
                "status": "INCOMPAT",
                "version": "unknown",
                "reason": "Docker test error",
            }
            print("    pyspark: INCOMPAT")
    else:
        results["pyspark"] = {
            "status": "SKIP",
            "version": "unknown",
            "reason": "Docker image not available",
        }
        print("    pyspark: SKIP (Docker image not found)")

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
        print(f"    airflow: PASS ({_af.__version__})")
    except ImportError:
        results["apache-airflow"] = {
            "status": "SKIP",
            "version": "not installed",
            "reason": "not installed",
        }
        print("    airflow: SKIP (not installed)")
    except Exception as e:
        results["apache-airflow"] = {
            "status": "INCOMPAT",
            "version": "unknown",
            "reason": str(e),
        }
        print(f"    airflow: INCOMPAT ({e})")

    return results


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
    py_ver = platform.python_version()
    manifest = {
        "project": "Python 3.15 Data Engineering Validation Suite",
        "release": release,
        "release_type": "beta" if "b" in release else "rc" if "rc" in release else "ga",
        "test_date": date.today().isoformat(),
        "platform": f"macOS {platform.mac_ver()[0]} ARM64",
        "python_build": f"cpython-{release}-macos-aarch64-none",
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
        "environment_consistent": not violations,
        "constraint_violations": list(violations or []),
        "results": results,
    }
    # Compute readiness inline (BLOCKED = upstream gap, partial credit)
    _eff = sum(counts.values()) - counts.get("SKIP", 0)
    _wp = counts["PASS"] + counts.get("BLOCKED", 0) * 0.3
    manifest["production_readiness_pct"] = (
        min(int((_wp / _eff) * 100), 95) if _eff else 0
    )
    # Defensive schema guarantee for downstream tests.
    manifest.setdefault("packages_blocked", counts.get("BLOCKED", 0))

    # print("\nDEBUG BEFORE WRITE")
    # print("packages_blocked =", manifest.get("packages_blocked"))
    # print(sorted(manifest.keys()))

    manifest_path = release_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

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
        "**Platform:** macOS 26.5 ARM64",
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

    (release_dir / "compatibility_report.md").write_text("\n".join(lines))


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
        "--docker-image",
        default=os.environ.get("DATAENG_DOCKER_IMAGE", "pyarrow-dataeng:py314"),
        help=(
            "Docker image for PySpark/PyArrow isolation "
            "(default: pyarrow-dataeng:py314, or DATAENG_DOCKER_IMAGE env var)"
        ),
    )
    args = parser.parse_args()

    release = args.release
    release_dir = REPORTS / release
    release_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating compatibility report for Python {release}")
    print(f"Output: {release_dir}")
    print("=" * 60)

    results = collect_results(docker_image=args.docker_image)
    violations = check_declared_support(results)
    counts = tally(results)

    print(
        f"\nResults: PASS={counts['PASS']}  FAIL={counts['FAIL']}  "
        f"INCOMPAT={counts['INCOMPAT']}  BLOCKED={counts.get('BLOCKED', 0)}  "
        f"SKIP={counts['SKIP']}"
    )
    if violations:
        print(f"Constraint violations: {len(violations)} (see manifest)")

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    write_manifest(release_dir, release, results, counts, violations=violations)
    write_compat_report(release_dir, release, results, counts)

    # Copy PDF if present
    pdf_src = REPO / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"
    if pdf_src.exists():
        shutil.copy2(pdf_src, release_dir / pdf_src.name)
        print(f"PDF copied to {release_dir.name}/")

    print(f"\nReport written to reports/{release}/")
    for f in sorted(release_dir.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size:,} bytes)")

    if args.auto_commit:
        run(f"git add reports/{release}/", capture=False)
        run(
            f'git commit -m "report: add {release} compatibility report"', capture=False
        )
        print(f"\nCommitted: report: add {release} compatibility report")


if __name__ == "__main__":
    main()
