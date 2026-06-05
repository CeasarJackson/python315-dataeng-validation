# Compatibility Reports

Versioned compatibility reports for each Python 3.15 test cycle.
Each subdirectory corresponds to a specific CPython release tested
against the data engineering validation suite.

---

## Report Index

| Release | Date | Production Readiness | Key Change |
|---------|------|---------------------|------------|
| [3.15.0b1](./3.15.0b1/compatibility_report.md) | June 2026 | 75% | Baseline report |
| [3.15.0b2](./3.15.0b2/) | Pending | — | Awaiting test cycle |

---

## Directory Structure

```
reports/
├── README.md                      # This index
├── 3.15.0b1/                      # Beta 1 results (complete)
│   ├── manifest.json              # Test metadata
├──   ├── compatibility_report.md    # Full compatibility table
│   ├── benchmark_summary.md       # Benchmark highlights
│   └── PYTHON315_DATAENG_READINESS_ASSESSMENT.pdf
├── 3.15.0b2/                      # Beta 2 (pending)
└── template/                      # Templates for new cycles
    ├── manifest.json
    └── compatibility_report.md
```

---

## Adding a New Report Cycle

```bash
# 1. Create the directory
mkdir reports/3.15.0rc1

# 2. Copy templates
cp reports/template/manifest.json reports/3.15.0rc1/
cp reports/template/compatibility_report.md reports/3.15.0rc1/

# 3. Run the full suite
python scripts/generate_report.py --release 3.15.0rc1

# 4. Review and commit
git add reports/3.15.0rc1/
git commit -m "report: add 3.15.0rc1 compatibility report"
```

Or use the automated generator which handles all of the above:

```bash
python scripts/generate_report.py --release 3.15.0rc1 --auto-commit
```

---

## Comparing Two Cycles

```bash
python scripts/compare_reports.py 3.15.0b1 3.15.0b2
```

---

*Dr. Ceasar Jackson Jr. — Python 3.15 Data Engineering Validation Suite*
