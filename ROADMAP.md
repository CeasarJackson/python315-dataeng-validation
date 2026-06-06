# Roadmap

## v1.3.0 ✔ Complete

- Airflow 3.2.2 validation suite
- Versioned compatibility report system
- generate_report.py / compare_reports.py automation
- RC validation (rc1, rc2)

## v1.4.0 ✔ Complete

- Prefect probe corrected (real import test)
- All INCOMPAT/SKIP reclassified correctly
- Final pre-GA baseline established
- PASS=14  FAIL=0  INCOMPAT=1  BLOCKED=2  SKIP=0
- Readiness: 75% (b1) → 85% (rc2)

## v1.5.0 — Planned

- benchmark_summary.md added to b2/rc1/rc2 report directories
- PYTHON315_DATAENG_VALIDATION.md updated with Airflow results
- per-library suite runner: run_all_validations.sh

## v2.0.0 — Waiting on PyArrow cp315 wheels

- Python 3.15 GA production assessment
- PyArrow BLOCKED → PASS
- dask.dataframe INCOMPAT → PASS
- ray BLOCKED → PASS (likely)
- Updated PDF readiness assessment
- Final compatibility report: 3.15.0ga
- Public release candidate

## Trigger for v2.0.0

```zsh
uv pip install pyarrow
.venv/bin/python scripts/generate_report.py --release 3.15.0ga --auto-commit
.venv/bin/python scripts/compare_reports.py 3.15.0rc2 3.15.0ga
git tag v2.0.0 -m "v2.0.0: Python 3.15 GA production assessment"
```
