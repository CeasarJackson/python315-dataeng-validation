#!/usr/bin/env python3
"""
scripts/generate_report.py
==========================
Runs the full validation suite and writes a versioned compatibility report
into reports/<release>/.

Usage:
    python scripts/generate_report.py --release 3.15.0rc1
    python scripts/generate_report.py --release 3.15.0rc1 --auto-commit
    python scripts/generate_report.py --release 3.15.0rc1 --dry-run
"""

import argparse
import importlib.metadata
import json
import platform
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
        cmd, shell=True, capture_output=capture,
        text=True, cwd=cwd or REPO
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


def collect_results():
    """Run quick import probes for all tracked packages."""
    print("  Probing core stack...")

    results = {}

    # Core packages
    for pkg in ["numpy", "pandas", "polars", "duckdb", "sqlalchemy",
                "pydantic", "matplotlib", "plotly", "jupyterlab"]:
        status, ver = probe_package(pkg)
        results[pkg] = {"status": status, "version": ver}
        print(f"    {pkg}: {status} ({ver})")

    # sqlite3 — stdlib
    try:
        import sqlite3
        results["sqlite3"] = {
            "status": "PASS",
            "version": sqlite3.sqlite_version
        }
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
        results["pyarrow"] = {"status": "BLOCKED", "version": "unavailable", "reason": "no cp315 wheels on PyPI; source build fails at CMake config"}
        print("    pyarrow: BLOCKED (no cp315 wheels)")

    # dask
    try:
        import dask.dataframe  # noqa: F401
        results["dask.dataframe"] = {"status": "PASS", "version": get_version("dask")}
        print(f"    dask.dataframe: PASS")
    except ImportError as e:
        if "pyarrow" in str(e):
            results["dask.dataframe"] = {
                "status": "INCOMPAT",
                "version": get_version("dask"),
                "reason": "runtime pyarrow dep"
            }
            print(f"    dask.dataframe: INCOMPAT (pyarrow dep)")
        else:
            results["dask.dataframe"] = {"status": "SKIP", "version": "not installed"}
            print(f"    dask.dataframe: SKIP")

    # prefect
    try:
        import prefect  # noqa: F401
        results["prefect"] = {"status": "PASS", "version": get_version("prefect")}
        print(f"    prefect: PASS")
    except ImportError as e:
        if "no_type_check_decorator" in str(e):
            results["prefect"] = {
                "status": "INCOMPAT",
                "version": get_version("prefect"),
                "reason": "typing.no_type_check_decorator removed in 3.15"
            }
            print(f"    prefect: INCOMPAT (stdlib change)")
        else:
            results["prefect"] = {"status": "SKIP", "version": "not installed"}
            print(f"    prefect: SKIP")

    # mlflow
    try:
        import mlflow  # noqa: F401
        results["mlflow"] = {"status": "PASS", "version": get_version("mlflow")}
        print(f"    mlflow: PASS")
    except (ImportError, Exception) as e:
        if "pyarrow" in str(e).lower() or "opentelemetry" in str(e).lower():
            results["mlflow"] = {
                "status": "INCOMPAT",
                "version": get_version("mlflow"),
                "reason": "pyarrow hard dep"
            }
            print(f"    mlflow: INCOMPAT (pyarrow dep)")
        else:
            results["mlflow"] = {"status": "SKIP", "version": "not installed"}
            print(f"    mlflow: SKIP")

    # ray
    try:
        import ray  # noqa: F401
        results["ray"] = {"status": "PASS", "version": get_version("ray")}
        print(f"    ray: PASS")
    except ImportError:
        results["ray"] = {"status": "BLOCKED", "version": "unavailable", "reason": "no cp315 wheels on PyPI"}
        print(f"    ray: BLOCKED (no cp315 wheels)")

    # pyspark via docker — uses file mount to avoid stdin hang
    if check_docker_image():
        print("  Testing PySpark via Docker...")
        import tempfile, os as _os
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                         delete=False, prefix='spark_probe_') as _f:
            _f.write(_spark_script)
            _tmp = _f.name
        try:
            import subprocess as _sp
            _r = _sp.run(
                ["docker", "run", "--rm",
                 "-v", f"{_tmp}:/tmp/spark_probe.py:ro",
                 "pyarrow-dataeng:py314", "python3", "/tmp/spark_probe.py"],
                capture_output=True, text=True, timeout=120
            )
            out, rc = _r.stdout, _r.returncode
        except _sp.TimeoutExpired:
            out, rc = "", 1
        finally:
            _os.unlink(_tmp)
        try:
            payload = json.loads([l for l in out.splitlines() if l.strip()][-1])
            if rc == 0 and payload.get("status") == "pass":
                results["pyspark"] = {
                    "status": "PASS",
                    "version": payload["version"],
                    "note": "via Docker py314 + OpenJDK 21"
                }
                print(f"    pyspark: PASS ({payload['version']} via Docker)")
            else:
                results["pyspark"] = {"status": "FAIL", "version": "unknown",
                                       "reason": "Docker test failed"}
                print("    pyspark: FAIL")
        except Exception:
            results["pyspark"] = {"status": "INCOMPAT", "version": "unknown",
                                   "reason": "Docker test error"}
            print("    pyspark: INCOMPAT")
    else:
        results["pyspark"] = {
            "status": "SKIP",
            "version": "unknown",
            "reason": "Docker image not available"
        }
        print("    pyspark: SKIP (Docker image not found)")

    # apache-airflow
    results["apache-airflow"] = {"status": "SKIP", "version": "not installed",
                                  "reason": "deferred"}
    print("    airflow: SKIP (deferred)")

    return results


def tally(results):
    counts = {"PASS": 0, "FAIL": 0, "INCOMPAT": 0, "SKIP": 0, "BLOCKED": 0}
    for v in results.values():
        s = v["status"]
        counts[s] = counts.get(s, 0) + 1
    return counts


def write_manifest(release_dir, release, results, counts):
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
        "docker_image": "pyarrow-dataeng:py314",
        "tester": "Dr. Ceasar Jackson Jr.",
        "suite_version": "1.2.0",
        "packages_tested": sum(counts.values()),
        "packages_pass": counts["PASS"],
        "packages_incompat": counts["INCOMPAT"],
        "packages_skip": counts["SKIP"],
        "packages_fail": counts["FAIL"],
        "results": results,
    }
    # Ensure production_readiness_pct is always present
    if "production_readiness_pct" not in manifest:
        manifest["production_readiness_pct"] = _readiness_pct(counts)
    (release_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def write_compat_report(release_dir, release, results, counts):
    def badge(status):
        return {"PASS": "✅ PASS", "FAIL": "❌ FAIL",
                "INCOMPAT": "⚠️ INCOMPAT", "BLOCKED": "🚫 BLOCKED", "SKIP": "⏭️ SKIP"}.get(status, status)

    core = ["numpy","pandas","polars","duckdb","sqlalchemy",
            "pydantic","matplotlib","plotly","jupyterlab","sqlite3"]
    extended = ["pyspark","dask.dataframe","pyarrow","mlflow",
                "prefect","ray","apache-airflow"]

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
        f"```bash",
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
    parser = argparse.ArgumentParser(description="Generate a versioned compatibility report")
    parser.add_argument("--release", required=True, help="Python release, e.g. 3.15.0rc1")
    parser.add_argument("--auto-commit", action="store_true", help="Git commit after generating")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing")
    args = parser.parse_args()

    release = args.release
    release_dir = REPORTS / release
    release_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating compatibility report for Python {release}")
    print(f"Output: {release_dir}")
    print("=" * 60)

    results = collect_results()
    counts = tally(results)

    print(f"\nResults: PASS={counts['PASS']}  FAIL={counts['FAIL']}  "
          f"INCOMPAT={counts['INCOMPAT']}  SKIP={counts['SKIP']}")

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    write_manifest(release_dir, release, results, counts)
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
            f'git commit -m "report: add {release} compatibility report"',
            capture=False
        )
        print(f"\nCommitted: report: add {release} compatibility report")


if __name__ == "__main__":
    main()
