# Python 3.15.2 - Readiness Reconciliation

**Author:** Dr. Ceasar Jackson Jr.
**Date:** 2026-10-27
**Platform:** macOS arm64
**Python:** 3.15.2 (Homebrew `python@3.15`)
**Status:** PROVISIONAL (local mode, single machine)

## 1. Summary

Every one of the 17 packages in the baseline now has a classification backed
by a workload that ran on Python 3.15.2, or a stated upstream blocker.

| Status | Count | Packages |
|---|---|---|
| PASS | 15 | numpy, pandas, polars, duckdb, sqlalchemy, pydantic, matplotlib, plotly, jupyterlab, sqlite3, pyarrow, dask.dataframe, prefect, pyspark, apache-airflow |
| BLOCKED | 2 | mlflow, ray (both upstream) |
| FAIL / INCOMPAT / SKIP | 0 | |

The readiness percentage is computed by `scripts/ingest_evidence.py` and
recorded in `manifest.reconciled.json`; it is not restated here.

## 2. Method

`scripts/generate_report.py` probes only the interpreter it runs in, so the
baseline (`manifest.baseline.json`, sha256
`b7e4668ed29cec839640243d69e34f88756b6e154f1f65832aa55f6feee6889a`, frozen
byte-identical to the generated `manifest.json`) records packages that live in
isolated environments as SKIP. Baseline: 11 PASS, 1 FAIL, 1 BLOCKED, 4 SKIP.
`evidence.json` states what was actually run for each package, at which
evidence level, and in which environment. PASS requires a workload that
executed on 3.15.2 (Functional or Integration).

## 3. Package evidence

| Package | Status | Version | Level | Evidence |
|---|---|---|---|---|
| numpy | PASS | 2.5.4 | Functional | core smoke 11/11 |
| pandas | PASS | 3.1.0 | Functional | core smoke 11/11 |
| polars | PASS | 1.41.2 | Functional | core smoke; validate_all suite |
| duckdb | PASS | 2.0.0 | Functional | core smoke; validate_all suite |
| sqlalchemy | PASS | 2.0.50 | Functional | core smoke; validate_all suite |
| pydantic | PASS | 2.14.1 | Functional | core smoke 11/11 |
| matplotlib | PASS | 3.11.2 | Functional | Agg render to PNG |
| plotly | PASS | 6.7.0 | Functional | figure build and JSON |
| sqlite3 | PASS | 3.54.1 | Functional | core smoke; validate_all suite |
| pyarrow | PASS | 26.0.0 | Functional | Parquet round-trip and interop |
| jupyterlab | PASS | 4.6.4 | Integration | isolated env, 101 packages, 5/5 probe |
| dask.dataframe | PASS | 2026.7.1 | Integration | Parquet round-trip in a notebook kernel |
| prefect | PASS | 3.9.0 | Functional | isolated and extended envs, all runs passed |
| pyspark | PASS | 4.2.0 | Functional | Docker `pyarrow-dataeng:py3152`, worker on 3.15.2 |
| apache-airflow | PASS | 3.3.2 | Functional | isolated env, 129 packages, `dags test` success |
| mlflow | BLOCKED | - | Resolution | pyarrow<26 cap vs. no cp315 wheel for 25.x |
| ray | BLOCKED | - | Resolution | no cp315 wheel (2.59.0: cp310-cp314) |

## 4. Notes by area

**Core.** The core smoke probe (Appendix A) passed 11/11 with zero captured
warnings. Its first run scored 9/11: two checks called
`Relation.fetchone()`, which DuckDB 2.0 removed, and a stray ResourceWarning
came from an SQLAlchemy engine the probe never disposed. Both were test-design
errors in the probe and are not counted against any package.

**Dask and JupyterLab.** JupyterLab 4.6.4 (3.15.1 had 4.5.7) with dask
2026.7.1 passed install, import, notebook execution through a registered
kernel, a Dask DataFrame Parquet round-trip and a kernel-isolation check.
`dask/config.py` opens a file without `encoding=`, which raises an
EncodingWarning under `-X warn_default_encoding`; harmless in 3.15's default
UTF-8 mode, upstream, informational. Jupyter warned that the kernel runs over
unencrypted TCP; no persistent server session or transport security was tested.

**Prefect.** 3.7.7 (the repository's old pin) is unusable: it requires
`starlette>=1.0.1` yet its server code calls `Body(..., min_items=1)`, which
FastAPI 0.162.0 rejects, and the last FastAPI that accepted it requires
`starlette<0.47`. This is a packaging conflict, not a Python 3.15 finding. 3.9.0
resolves with FastAPI 0.150.0 and passed flow, task, retry-recovery and
aggregation checks in every run. Two kinds of log noise appeared in some runs
and never changed a result: a `database is locked` error from the telemetry
heartbeat (absent when telemetry is disabled) and intermittent `EventsWorker`
errors with "Cannot put items in a stopped service instance". The EventsWorker
errors reproduced identically on Python 3.14.10 with the same Prefect version
during the 3.15.1 cycle; no 3.14 control was rerun for 3.15.2. Root cause
undetermined.

**Airflow.** 3.3.2 installed with 129 packages and a clean integrity check.
`db migrate` and `dags test` succeeded on a two-task DAG (XCom value 120,
Python 3.15.2), and one dag-processor run registered the DAG with no import
errors. `dags test` runs tasks in-process; the scheduler and api-server were
not exercised. Binary-only resolution fails only because PyYAML 6.0.3 is
published as a source distribution; the install builds it from source.

**PySpark.** Evidence comes from the `python:3.15.2-slim` Docker image, local
mode only. The baseline probe confirmed the worker interpreter as 3.15.2.

**MLflow.** The binary-only resolve on a fresh 3.15.2 venv failed because no
pyarrow release up to 25.0.1 has a cp315 wheel and every MLflow release from
3.15.0 caps `pyarrow<26`. pyarrow 26.0.0 has a wheel but the cap excludes it.
The workarounds recorded for 3.15.1 (mlflow-skinny; full MLflow with a
`pyarrow>=26` override, which fails `uv pip check`) were not re-run.

**Ray.** ray 2.59.0 publishes cp310 to cp314 wheels, none for cp315.

## 5. Test-design errors not counted

- Baseline FAIL for jupyterlab: the core environment does not carry it.
- Probe errors listed under Core above.
- An earlier binary-only Airflow dry-run failed on PyYAML being sdist-only and
  an MLflow override dry-run used a flag broader than the 3.15.1 method; both
  were discarded and Airflow was retested with the 3.15.1 method.

## 6. Environments

| Environment | Packages | Purpose |
|---|---|---|
| `.venv3152` | 30 | core stack (`requirements-py315-core-3.15.2.lock.txt`) |
| `.venv3152-extended` | 127 | dask 2026.7.1 + prefect 3.9.0 (`requirements-py315-extended-3.15.2.lock.txt`) |
| isolated, temporary | 103 / 129 / 101 | Prefect, Airflow, JupyterLab (discarded after the run) |
| `pyarrow-dataeng:py3152` | - | PySpark, `python:3.15.2-slim` |

All `uv pip check` runs were clean, and the core freeze was identical before
and after every extended install.

## 7. Not tested

Production Jupyter server or security, distributed Dask, Spark cluster mode,
Airflow scheduler and api-server, MLflow server and registry, performance,
other operating systems and architectures.

## 8. Provenance

Times are EDT, 2026-10-27, from terminal output.

| Time | Experiment |
|---|---|
| 12:19, 12:42 | Prefect 3.9.0, isolated env |
| 12:45 to 12:51 | Dask and Prefect, extended env |
| 12:51 | Airflow install and `dags test` |
| about 12:55 | JupyterLab integration probe (exact time not captured) |
| 12:56 | Airflow dag-processor registration |
| 12:57 | Scaffold and baseline report |
| 13:02 | Core smoke probe, 11/11 |

## Appendix A - core smoke probe

Run with `.venv3152/bin/python - <<'PY' ... PY`; writes only to a temp directory.

```python
import io, json, sqlite3, sys, tempfile, warnings
from pathlib import Path

assert sys.version.startswith("3.15.2"), sys.version
results = {}
tmp = Path(tempfile.mkdtemp(prefix="core3152_"))

def check(name, fn):
    try:
        fn()
        results[name] = "PASS"
    except Exception as exc:
        results[name] = "FAIL: %s: %s" % (type(exc).__name__, exc)

def numpy_():
    import numpy as np
    assert np.arange(1, 16).sum() == 120
    assert float(np.linalg.norm(np.array([3.0, 4.0]))) == 5.0

def pandas_():
    import pandas as pd
    df = pd.DataFrame({"k": list("aabb"), "v": [10, 20, 30, 60]})
    assert df.groupby("k").v.sum().to_dict() == {"a": 30, "b": 90}
    assert df.v.sum() == 120

def polars_():
    import polars as pl
    df = pl.DataFrame({"k": list("aabb"), "v": [10, 20, 30, 60]})
    assert df.group_by("k").agg(pl.col("v").sum()).sort("k")["v"].to_list() == [30, 90]

def duckdb_():
    import duckdb
    rows = duckdb.sql("select sum(v) from (values (10),(20),(30),(60)) t(v)").fetchall()
    assert rows[0][0] == 120

def sqlalchemy_():
    from sqlalchemy import create_engine, text
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as c:
            c.execute(text("create table t(v int)"))
            c.execute(text("insert into t values (10),(20),(30),(60)"))
            assert c.execute(text("select sum(v) from t")).scalar() == 120
    finally:
        engine.dispose()

def pydantic_():
    from pydantic import BaseModel, ValidationError
    class M(BaseModel):
        x: int
    assert M(x="5").x == 5
    try:
        M(x="not-a-number")
    except ValidationError:
        return
    raise AssertionError("invalid input was accepted")

def matplotlib_():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure()
    plt.plot([1, 2, 3])
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    assert buf.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"

def plotly_():
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(x=["a", "b"], y=[30, 90]))
    assert json.loads(fig.to_json())["data"][0]["y"] == [30, 90]

def pyarrow_():
    import pyarrow as pa, pyarrow.parquet as pq
    path = tmp / "t.parquet"
    pq.write_table(pa.table({"v": [10, 20, 30, 60]}), path)
    assert sum(pq.read_table(path).column("v").to_pylist()) == 120

def interop_():
    import duckdb, pandas as pd, polars as pl, pyarrow as pa
    t = pa.Table.from_pandas(pd.DataFrame({"v": [10, 20, 30, 60]}))
    assert pl.from_arrow(t)["v"].sum() == 120
    assert duckdb.sql("select sum(v) from t").fetchall()[0][0] == 120

def sqlite_():
    con = sqlite3.connect(tmp / "t.db")
    try:
        con.execute("create table t(v int)")
        con.executemany("insert into t values (?)", [(10,), (20,), (30,), (60,)])
        con.commit()
        assert con.execute("select sum(v) from t").fetchone()[0] == 120
    finally:
        con.close()
    print("sqlite3 library:", sqlite3.sqlite_version)

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for name, fn in [("numpy", numpy_), ("pandas", pandas_), ("polars", polars_),
                     ("duckdb", duckdb_), ("sqlalchemy", sqlalchemy_),
                     ("pydantic", pydantic_), ("matplotlib", matplotlib_),
                     ("plotly", plotly_), ("pyarrow", pyarrow_),
                     ("arrow/pandas/polars/duckdb interop", interop_),
                     ("sqlite3", sqlite_)]:
        check(name, fn)
    import gc; gc.collect()

for name, res in results.items():
    print("%-38s %s" % (name, res))
print("warnings captured:", len(caught))
n = sum(v == "PASS" for v in results.values())
print("CORE SMOKE: %d/11 PASS" % n)
sys.exit(0 if n == 11 else 1)
```
