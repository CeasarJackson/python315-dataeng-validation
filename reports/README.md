# Compatibility Reports

Versioned compatibility reports for each Python 3.15 test cycle.
Each subdirectory corresponds to a specific CPython release tested
against the data engineering validation suite.

---

## Report Index

| Release | Date | Readiness | Key Change |
|---------|------|-----------|------------|
| [3.15.0b1](./3.15.0b1/compatibility_report.md) | 2026-06-04 | 75% | Baseline |
| [3.15.0b2](./3.15.0b2/compatibility_report.md) | 2026-06-05 | 85% | Prefect + MLflow → PASS |
| [3.15.0rc1](./3.15.0rc1/compatibility_report.md) | 2026-06-05 | 85% | No regressions |
| [3.15.0rc2](./3.15.0rc2/compatibility_report.md) | 2026-06-05 | 85% | No regressions |
| [v1.8.0](./v1.8.0/compatibility_report.md) | 2026-06-06 | 87% | Unified validation + release automation |
| [v1.8.1](./v1.8.1/compatibility_report.md) | 2026-06-06 | 87% | Readiness artifacts synchronized |
| 3.15.0ga | Pending | — | Awaiting PyArrow cp315 wheels + GA release |

---

## Arc Summary: Beta → RC

```
3.15.0b1  75%  •  baseline — 4 INCOMPAT, 0 BLOCKED classified
3.15.0b2  85%  •  prefect PASS, mlflow PASS, pyarrow/ray reclassified BLOCKED
3.15.0rc1 85%  •  no changes from b2
3.15.0rc2 85%  •  Prefect probe corrected; PASS=14 FAIL=0 INCOMPAT=1 BLOCKED=2
v1.8.0   87%  •  unified validation runner + automated release packaging
v1.8.1   87%  •  readiness assessment synchronization and reporting fixes
```

The remaining readiness gap is driven by upstream ecosystem dependencies.
PyArrow cp315 wheels are not yet available, which blocks portions of the
Arrow-based analytics stack. Once official wheels are published,
dask.dataframe and related Arrow-dependent tooling are expected to move
from BLOCKED/INCOMPAT to PASS without requiring code changes in this
validation suite.

---

## Status Taxonomy

| Status | Meaning |
|--------|---------|
| ✅ PASS | Installed and fully functional |
| ⚠️ INCOMPAT | Installed but broken by dependency chain |
| 🚫 BLOCKED | Upstream infrastructure gap (no wheels) — not a code defect |
| ⏭️ SKIP | Not tested this cycle |
| ❌ FAIL | Installed but produces wrong results or crashes |

---

## Directory Structure

```
reports/
├── README.md                          # This index
├── 3.15.0b1/                          # Beta 1 (complete)
│   ├── manifest.json
│   ├── compatibility_report.md
│   ├── benchmark_summary.md
│   └── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf
├── 3.15.0b2/                          # Beta 2 (complete)
│   ├── manifest.json
│   ├── compatibility_report.md
│   ├── executive_summary.md
│   ├── full_readiness_assessment.md
│   ├── readiness_matrix.md
│   ├── readiness_matrix.json
│   └── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf
├── 3.15.0rc1/                         # RC 1 (complete)
├── 3.15.0rc2/                         # RC 2 (complete)
├── v1.8.0/                            # Automated release package
├── v1.8.1/                            # Reporting synchronization release
├── 3.15.0ga/                          # GA (pending)
└── template/                          # Templates for new cycles
    ├── manifest.json
    └── compatibility_report.md
```

---

## Running a New Cycle

```bash
# Generate report and auto-commit
python scripts/generate_report.py --release 3.15.0ga --auto-commit

# Compare with previous cycle
python scripts/compare_reports.py 3.15.0rc2 3.15.0ga

# Dry run (no files written)
python scripts/generate_report.py --release 3.15.0ga --dry-run
```

---

## Comparing Any Two Cycles

```bash
# Adjacent cycles
python scripts/compare_reports.py 3.15.0b1 3.15.0b2

# Full arc
python scripts/compare_reports.py 3.15.0b1 3.15.0rc2

# Markdown output (for publishing)
python scripts/compare_reports.py 3.15.0b1 3.15.0rc2 --format markdown
```

---

*Dr. Ceasar Jackson Jr. — Python 3.15 Data Engineering Validation Suite*

Repository Status: Production-ready validation framework with automated testing, reporting, packaging, release generation, and readiness assessment workflows for Python 3.15 ecosystem tracking.
