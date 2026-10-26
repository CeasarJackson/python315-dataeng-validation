#!/usr/bin/env python3
"""
==============================================================================
Python 3.15 Data Engineering Validation Lab
==============================================================================
Test Suite:
    test_generate_report_provenance.py

Author:
    Dr. Ceasar Jackson Jr.

Purpose:
    Protect report generation from interpreter-environment leakage and stale
    platform metadata.

Validation:
    python -m py_compile tests/test_generate_report_provenance.py
    python -m pytest tests/test_generate_report_provenance.py -v

==============================================================================
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_report.py"


def load_generator():
    """Load generate_report.py as an importable test module."""
    spec = importlib.util.spec_from_file_location(
        "generate_report_under_test",
        GENERATOR_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_support_targets_running_interpreter(monkeypatch) -> None:
    """uv pip check must explicitly target the interpreter running the report."""
    generator = load_generator()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(generator.subprocess, "run", fake_run)

    results = {
        "prefect": {
            "status": "PASS",
            "version": "3.7.7",
        }
    }

    violations = generator.check_declared_support(results)

    assert violations == []
    assert captured["cmd"] == [
        "uv",
        "pip",
        "check",
        "--python",
        sys.executable,
    ]


def test_declared_python_constraint_downgrades_pass(monkeypatch) -> None:
    """A package that excludes the runtime must not remain PASS."""
    generator = load_generator()

    output = (
        "Found 1 incompatibility\n"
        "The package `prefect` requires Python >=3.10, <3.15, "
        "but `3.15.0rc2` is installed\n"
    )

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr=output)

    monkeypatch.setattr(generator.subprocess, "run", fake_run)

    results = {
        "prefect": {
            "status": "PASS",
            "version": "3.7.7",
        }
    }

    violations = generator.check_declared_support(results)

    assert len(violations) == 1
    assert results["prefect"]["status"] == "INCOMPAT"
    assert results["prefect"]["version"] == "3.7.7"
    assert "declared unsupported" in results["prefect"]["reason"]


def test_compat_report_uses_live_platform(tmp_path, monkeypatch) -> None:
    """Compatibility Markdown must derive platform data at generation time."""
    generator = load_generator()

    monkeypatch.setattr(generator.platform, "mac_ver", lambda: ("26.6.2", (), ""))
    monkeypatch.setattr(generator.platform, "machine", lambda: "arm64")

    results = {
        "numpy": {"status": "PASS", "version": "2.4.6"},
    }

    counts = {
        "PASS": 1,
        "FAIL": 0,
        "INCOMPAT": 0,
        "BLOCKED": 0,
        "SKIP": 0,
    }

    generator.write_compat_report(
        tmp_path,
        "3.15.0rc2",
        results,
        counts,
    )

    report = (tmp_path / "compatibility_report.md").read_text(encoding="utf-8")

    assert "**Platform:** macOS 26.6.2 arm64" in report
    assert "macOS 26.5 ARM64" not in report


def test_generator_does_not_copy_legacy_root_pdf() -> None:
    """Versioned reports must not silently inherit the legacy root PDF."""
    source = GENERATOR_PATH.read_text(encoding="utf-8")

    assert 'REPO / "PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf"' not in source
    assert "shutil.copy2" not in source


def test_generator_readiness_matches_canonical_weighting() -> None:
    source = Path("scripts/generate_report.py").read_text(encoding="utf-8")

    assert 'counts.get("BLOCKED", 0) * 0.50' in source
    assert 'counts.get("INCOMPAT", 0) * 0.25' in source
    assert "round((_wp / _eff) * 100)" in source
    assert 'counts.get("BLOCKED", 0) * 0.3' not in source


# Phase 1 regressions use only mocks and isolated temporary report directories.


@pytest.mark.parametrize(
    ("rc", "stdout", "stderr", "status"),
    [
        (0, "", "All installed packages are compatible", "PASS"),
        (1, "", "The package `prefect` requires Python <3.15", "FAIL"),
        (0, "The package `prefect` requires Python <3.15", "", "FAIL"),
        (1, "", "resolver failed", "UNKNOWN"),
        (2, "partial output", "internal error", "UNKNOWN"),
        (1, "Found 1 incompatibility", "unrecognized detail", "FAIL"),
        (0, "Found unknown result", "unrecognized detail", "UNKNOWN"),
        (0, "unexpected diagnostic", "", "UNKNOWN"),
    ],
)
def test_dependency_outcomes(monkeypatch, rc, stdout, stderr, status):
    generator = load_generator()
    monkeypatch.setattr(
        generator.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=rc, stdout=stdout, stderr=stderr),
    )
    check = generator.check_declared_support({})
    assert check.status == status
    assert check.returncode == rc
    assert check.stdout == stdout
    assert check.stderr == stderr


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("uv missing"),
        subprocess.TimeoutExpired("uv", 60, output=b"partial", stderr=b"timed out"),
    ],
)
def test_dependency_execution_errors(monkeypatch, error):
    generator = load_generator()

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(generator.subprocess, "run", fail)
    check = generator.check_declared_support({})
    assert check.status == "UNKNOWN"
    assert check.returncode is None
    assert type(error).__name__ in check.error
    if isinstance(error, subprocess.TimeoutExpired):
        assert check.stdout == "partial"
        assert check.stderr == "timed out"


@pytest.mark.parametrize(
    ("status", "rc", "violations", "consistent"),
    [
        ("PASS", 0, [], True),
        ("FAIL", 1, ["violation"], False),
        ("FAIL", 1, [], False),
        ("UNKNOWN", 2, [], None),
        ("PASS", 2, [], None),
        ("PASS", 0, ["violation"], False),
    ],
)
def test_manifest_dependency_consistency(tmp_path, status, rc, violations, consistent):
    generator = load_generator()
    check = generator.DependencyCheck(
        violations, status=status, returncode=rc, stdout="output", stderr="diagnostic"
    )
    generator.write_manifest(
        tmp_path, "3.15.0", {}, generator.tally({}), violations=check
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["environment_consistent"] is consistent
    assert manifest["constraint_violations"] == violations
    assert manifest["dependency_check"]["returncode"] == rc
    assert manifest["dependency_check"]["stderr"] == "diagnostic"
    assert (manifest["dependency_check"]["status"] == "PASS") is (consistent is True)


@pytest.mark.parametrize("violations", [None, []])
def test_legacy_empty_violations_are_unknown(tmp_path, violations):
    generator = load_generator()
    generator.write_manifest(
        tmp_path, "3.15.0", {}, generator.tally({}), violations=violations
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["environment_consistent"] is None
    assert manifest["dependency_check"]["status"] == "UNKNOWN"


def configure_main(generator, monkeypatch, reports, *extra):
    monkeypatch.setattr(generator, "REPORTS", reports)
    # main() attaches the shared logger. Tests must never write into the real
    # logs/ directory, so force the console-only sink while keeping the real
    # configuration code path (the dry-run test reads the console output).
    real_configure = generator._configure_logging
    monkeypatch.setattr(
        generator,
        "_configure_logging",
        lambda file_logging=True: real_configure(file_logging=False),
    )
    monkeypatch.setattr(
        sys, "argv", ["generate_report.py", "--release", "3.15.0", *extra]
    )


def forbidden(*args, **kwargs):
    raise AssertionError("Operational action must not run")


@pytest.mark.parametrize("populated", [True, False])
def test_main_refuses_existing_report_before_probes(tmp_path, monkeypatch, populated):
    generator = load_generator()
    release = tmp_path / "3.15.0"
    release.mkdir()
    if populated:
        (release / "manifest.json").write_bytes(b"historical evidence")
    configure_main(generator, monkeypatch, tmp_path)
    monkeypatch.setattr(generator, "collect_results", forbidden)
    with pytest.raises(SystemExit) as exc:
        generator.main()
    assert exc.value.code == 2
    if populated:
        assert (release / "manifest.json").read_bytes() == b"historical evidence"


@pytest.mark.parametrize(
    "writer,name",
    [
        ("write_manifest", "manifest.json"),
        ("write_compat_report", "compatibility_report.md"),
    ],
)
def test_direct_writers_refuse_overwrite(tmp_path, writer, name):
    generator = load_generator()
    (tmp_path / name).write_bytes(b"evidence")
    with pytest.raises(FileExistsError):
        getattr(generator, writer)(tmp_path, "3.15.0", {}, generator.tally({}))
    assert (tmp_path / name).read_bytes() == b"evidence"


def staged_report(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    for name in ("manifest.json", "compatibility_report.md"):
        (staging / name).write_text(name, encoding="utf-8")
    return staging


def test_publication_into_scaffold_preserves_documents(tmp_path):
    generator = load_generator()
    staging = staged_report(tmp_path)
    destination = tmp_path / "3.15.1"
    destination.mkdir()

    originals = {}
    for name in generator.SCAFFOLD_FILES:
        content = f"preserve: {name}"
        (destination / name).write_text(content, encoding="utf-8")
        originals[name] = content

    assert generator.is_scaffold_only_directory(destination)

    generator.publish_artifacts(staging, destination)

    assert (destination / "manifest.json").read_text(
        encoding="utf-8"
    ) == "manifest.json"
    assert (destination / "compatibility_report.md").read_text(
        encoding="utf-8"
    ) == "compatibility_report.md"

    assert {
        name: (destination / name).read_text(encoding="utf-8") for name in originals
    } == originals

    with pytest.raises(FileExistsError):
        generator.publish_artifacts(staging, destination)


def test_scaffold_publication_failure_preserves_documents(tmp_path, monkeypatch):
    generator = load_generator()
    staging = staged_report(tmp_path)
    destination = tmp_path / "3.15.1"
    destination.mkdir()

    for name in generator.SCAFFOLD_FILES:
        (destination / name).write_text(name, encoding="utf-8")

    real_link = generator.os.link
    calls = 0

    def fail_second_link(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("publication failure")
        return real_link(source, target)

    monkeypatch.setattr(generator.os, "link", fail_second_link)

    with pytest.raises(OSError, match="publication failure"):
        generator.publish_artifacts(staging, destination)

    assert {p.name for p in destination.iterdir()} == generator.SCAFFOLD_FILES

    for name in generator.SCAFFOLD_FILES:
        assert (destination / name).read_text(encoding="utf-8") == name


def test_scaffold_recognition_rejects_unexpected_files(tmp_path):
    generator = load_generator()
    destination = tmp_path / "3.15.1"
    destination.mkdir()

    for name in generator.SCAFFOLD_FILES:
        (destination / name).write_text(name, encoding="utf-8")

    (destination / "unexpected.txt").write_text("preserve", encoding="utf-8")

    assert not generator.is_scaffold_only_directory(destination)

    with pytest.raises(FileExistsError):
        generator.publish_artifacts(staged_report(tmp_path), destination)

    assert (destination / "unexpected.txt").read_text(encoding="utf-8") == "preserve"


def test_publication_success_and_refusal(tmp_path):
    generator = load_generator()
    staging = staged_report(tmp_path)
    destination = tmp_path / "release"
    generator.publish_artifacts(staging, destination)
    assert {p.name: p.read_text(encoding="utf-8") for p in destination.iterdir()} == {
        p.name: p.read_text(encoding="utf-8") for p in staging.iterdir()
    }
    with pytest.raises(FileExistsError):
        generator.publish_artifacts(staging, destination)
    assert (destination / "manifest.json").read_text(
        encoding="utf-8"
    ) == "manifest.json"


@pytest.mark.parametrize("failure_call", [1, 2])
def test_publication_failure_rolls_back_own_files(tmp_path, monkeypatch, failure_call):
    generator = load_generator()
    staging = staged_report(tmp_path)
    destination = tmp_path / "release"
    real_link = generator.os.link
    calls = 0

    def failing_link(source, target):
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("publication failure")
        real_link(source, target)

    monkeypatch.setattr(generator.os, "link", failing_link)
    with pytest.raises(OSError, match="publication failure"):
        generator.publish_artifacts(staging, destination)
    assert not destination.exists()
    assert len(list(staging.iterdir())) == 2


def test_publication_preserves_unexpected_evidence(tmp_path, monkeypatch):
    generator = load_generator()
    staging = staged_report(tmp_path)
    destination = tmp_path / "release"

    def concurrent_file(source, target):
        target.write_text("unexpected evidence", encoding="utf-8")
        raise FileExistsError(target)

    monkeypatch.setattr(generator.os, "link", concurrent_file)
    with pytest.raises(FileExistsError):
        generator.publish_artifacts(staging, destination)
    assert (destination / "compatibility_report.md").read_text(
        encoding="utf-8"
    ) == "unexpected evidence"


def test_generation_failure_never_publishes(tmp_path, monkeypatch):
    generator = load_generator()
    reports = tmp_path / "reports"
    reports.mkdir()
    historical = reports / "old"
    historical.mkdir()
    (historical / "manifest.json").write_bytes(b"evidence")
    configure_main(generator, monkeypatch, reports)
    monkeypatch.setattr(generator, "verify_release_matches_runtime", lambda *a: None)
    monkeypatch.setattr(generator, "collect_results", lambda **kw: {})
    monkeypatch.setattr(
        generator, "check_declared_support", lambda *a: generator.DependencyCheck()
    )

    def fail(*args):
        raise OSError("generation failure")

    monkeypatch.setattr(generator, "write_compat_report", fail)
    with pytest.raises(OSError, match="generation failure"):
        generator.main()
    assert list(reports.iterdir()) == [historical]
    assert (historical / "manifest.json").read_bytes() == b"evidence"


def test_dry_run_never_writes_or_probes(tmp_path, monkeypatch, capsys):
    generator = load_generator()
    configure_main(
        generator,
        monkeypatch,
        tmp_path / "absent" / "reports",
        "--dry-run",
        "--auto-commit",
    )
    for name in (
        "collect_results",
        "check_declared_support",
        "verify_release_matches_runtime",
        "write_manifest",
        "write_compat_report",
        "publish_artifacts",
        "run",
    ):
        monkeypatch.setattr(generator, name, forbidden)
    monkeypatch.setattr(generator.subprocess, "run", forbidden)
    monkeypatch.setattr(generator.tempfile, "TemporaryDirectory", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    generator.main()
    assert list(tmp_path.iterdir()) == []
    assert "No probes run or files written" in capsys.readouterr().out


@pytest.mark.parametrize("fail_publication", [False, True])
def test_main_staging_and_publication(tmp_path, monkeypatch, fail_publication):
    generator = load_generator()
    reports = tmp_path / "reports"
    configure_main(generator, monkeypatch, reports, "--docker-image", "custom-image")
    monkeypatch.setattr(generator, "verify_release_matches_runtime", lambda *a: None)
    monkeypatch.setattr(generator, "collect_results", lambda **kw: {})
    monkeypatch.setattr(
        generator,
        "check_declared_support",
        lambda *a: generator.DependencyCheck(status="PASS", returncode=0),
    )
    if fail_publication:

        def fail(*args):
            raise OSError("publication failure")

        monkeypatch.setattr(generator.os, "link", fail)
        with pytest.raises(OSError, match="publication failure"):
            generator.main()
        assert list(reports.iterdir()) == []
    else:
        generator.main()
        assert [p.name for p in reports.iterdir()] == ["3.15.0"]
        manifest = json.loads(
            (reports / "3.15.0" / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["environment_consistent"] is True
        assert manifest["docker_image"] == "custom-image"


@pytest.mark.parametrize("release", ["../old", "/tmp/report", "3.15.0/old"])
def test_release_cannot_escape_reports(tmp_path, monkeypatch, release):
    generator = load_generator()
    monkeypatch.setattr(sys, "argv", ["generate_report.py", "--release", release])
    monkeypatch.setattr(generator, "collect_results", forbidden)
    monkeypatch.setattr(generator, "REPORTS", tmp_path)
    with pytest.raises(SystemExit) as exc:
        generator.main()
    assert exc.value.code == 2
    assert list(tmp_path.iterdir()) == []
