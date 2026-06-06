"""
================================================================================
validate_stack.py — Phase 2: Data Engineering Lite Stack Validation
================================================================================
Project  : Python 3.15 Data Engineering Validation Suite
Author   : Dr. Ceasar Jackson Jr.
Platform : macOS 26.5 ARM64
Manager  : uv
================================================================================

PURPOSE
-------
Validates the full data engineering lite stack under Python 3.15.  Goes beyond
simple imports: each package is exercised with a representative smoke test to
confirm runtime correctness, not just install completeness.

WHAT IS TESTED
--------------
  numpy   — Array creation, dtype inference, vectorized arithmetic
  pandas  — DataFrame construction, groupby, CSV round-trip
  polars  — LazyFrame construction, filter, collect
  duckdb  — In-memory SQL: CREATE TABLE, INSERT, SELECT, aggregation
  sqlalchemy — Engine creation, metadata reflection (SQLite in-memory)
  pydantic   — Model definition, validation, .model_dump()
  matplotlib — Figure creation, Axes, savefig (non-interactive Agg backend)
  plotly     — go.Figure construction, .to_json() serialization
  tqdm       — Progress bar iteration over a small list

EXPECTED OUTCOME
----------------
  All checks [PASS] with exit code 0.
  A timestamped log is written to logs/validate_stack.log.

USAGE
-----
  python scripts/validate_stack.py

EXIT CODES
----------
  0 — All packages validated
  1 — One or more packages failed import or smoke test

NOTES
-----
  - matplotlib is tested in non-interactive mode (Agg backend) to avoid
    display requirements in headless CI environments.
  - DuckDB tests use an in-memory database (:memory:) — no files are written.
  - The SQLAlchemy test uses sqlite:// which requires only stdlib sqlite3.
  - tqdm output is suppressed (file=open(os.devnull)) to keep log output clean;
    only the timing result is logged.
================================================================================
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap path so logger.py resolves when run directly
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger  # noqa: E402

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Minimum acceptable versions for each package.
# Update these as the project matures.
# ---------------------------------------------------------------------------
MIN_VERSIONS: dict[str, tuple[int, ...]] = {
    "numpy": (2, 0, 0),
    "pandas": (2, 0, 0),
    "polars": (1, 0, 0),
    "duckdb": (1, 0, 0),
}


# ---------------------------------------------------------------------------
# Version helper
# ---------------------------------------------------------------------------


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '2.4.6' into a comparable tuple."""
    try:
        return tuple(int(x) for x in version_str.split(".")[:3])
    except (ValueError, AttributeError):
        return (0,)


def _check_min_version(package: str, version_str: str) -> None:
    """Log a warning if the installed version is below the minimum."""
    if package not in MIN_VERSIONS:
        return
    installed = _parse_version(version_str)
    minimum = MIN_VERSIONS[package]
    if installed < minimum:
        log.warning(
            "[WARN] %s %s is below minimum %s — upgrade recommended",
            package,
            version_str,
            ".".join(str(x) for x in minimum),
        )


# ---------------------------------------------------------------------------
# Individual smoke tests — each returns True on pass, False on fail.
# ---------------------------------------------------------------------------


def test_numpy() -> bool:
    """Import numpy and validate array operations."""
    try:
        import numpy as np  # noqa: PLC0415

        _check_min_version("numpy", np.__version__)
        log.info("[PASS] numpy %s — imported", np.__version__)

        # Basic array creation and arithmetic
        a = np.arange(1_000_000, dtype=np.float64)
        result = np.sqrt(a).mean()
        log.debug("numpy smoke: sqrt(arange(1M)).mean() = %.4f", result)
        log.info("[PASS] numpy — vectorized arithmetic OK")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] numpy — %s", exc)
        return False


def test_pandas() -> bool:
    """Import pandas, build a DataFrame, run groupby, round-trip to CSV."""
    try:
        import pandas as pd  # noqa: PLC0415

        _check_min_version("pandas", pd.__version__)
        log.info("[PASS] pandas %s — imported", pd.__version__)

        # DataFrame construction
        df = pd.DataFrame(
            {
                "region": ["north", "south", "north", "south", "north"],
                "sales": [120, 85, 200, 95, 160],
                "returns": [5, 3, 8, 2, 7],
            }
        )

        # Groupby aggregation
        summary = df.groupby("region")["sales"].sum()
        log.debug("pandas groupby result:\n%s", summary.to_string())
        log.info("[PASS] pandas — DataFrame + groupby OK")

        # CSV round-trip via StringIO (no file I/O required)
        import io  # noqa: PLC0415

        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        df2 = pd.read_csv(buf)
        assert df.shape == df2.shape, "CSV round-trip shape mismatch"
        log.info("[PASS] pandas — CSV round-trip OK")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] pandas — %s", exc)
        return False


def test_polars() -> bool:
    """Import polars and validate LazyFrame operations."""
    try:
        import polars as pl  # noqa: PLC0415

        _check_min_version("polars", pl.__version__)
        log.info("[PASS] polars %s — imported", pl.__version__)

        # LazyFrame construction and filter/collect
        lf = pl.LazyFrame(
            {
                "product": ["A", "B", "C", "A", "B"],
                "qty": [10, 20, 5, 15, 25],
                "price": [1.5, 2.0, 3.5, 1.5, 2.0],
            }
        )
        result = (
            lf.filter(pl.col("qty") > 10)
            .with_columns((pl.col("qty") * pl.col("price")).alias("revenue"))
            .collect()
        )
        log.debug("polars LazyFrame result:\n%s", result)
        log.info("[PASS] polars — LazyFrame filter + collect OK (%d rows)", len(result))
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] polars — %s", exc)
        return False


def test_duckdb() -> bool:
    """Import duckdb and validate in-memory SQL operations."""
    try:
        import duckdb  # noqa: PLC0415

        _check_min_version("duckdb", duckdb.__version__)
        log.info("[PASS] duckdb %s — imported", duckdb.__version__)

        # In-memory database operations
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE sales (
                id      INTEGER,
                region  VARCHAR,
                amount  DOUBLE
            )
        """)
        con.executemany(
            "INSERT INTO sales VALUES (?, ?, ?)",
            [(1, "west", 1500.0), (2, "east", 2200.0), (3, "west", 800.0)],
        )
        rows = con.execute(
            "SELECT region, SUM(amount) AS total FROM sales GROUP BY region ORDER BY total DESC"
        ).fetchall()
        log.debug("duckdb aggregation result: %s", rows)
        assert len(rows) == 2, "Expected 2 region groups"
        log.info("[PASS] duckdb — in-memory CREATE/INSERT/GROUP BY OK")
        con.close()
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] duckdb — %s", exc)
        return False


def test_sqlalchemy() -> bool:
    """Import SQLAlchemy and create an in-memory SQLite engine."""
    try:
        import sqlalchemy as sa  # noqa: PLC0415

        log.info("[PASS] sqlalchemy %s — imported", sa.__version__)

        engine = sa.create_engine("sqlite:///:memory:", echo=False)
        metadata = sa.MetaData()
        orders = sa.Table(
            "orders",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("customer", sa.String),
            sa.Column("total", sa.Float),
        )
        metadata.create_all(engine)

        with engine.connect() as conn:
            conn.execute(
                orders.insert(),
                [
                    {"id": 1, "customer": "Alice", "total": 99.99},
                    {"id": 2, "customer": "Bob", "total": 149.50},
                ],
            )
            conn.commit()
            result = conn.execute(sa.select(orders)).fetchall()

        assert len(result) == 2, "Expected 2 rows"
        log.info("[PASS] sqlalchemy — engine + Table + INSERT + SELECT OK")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] sqlalchemy — %s", exc)
        return False


def test_pydantic() -> bool:
    """Import pydantic and validate model definition and parsing."""
    try:
        import pydantic  # noqa: PLC0415

        log.info("[PASS] pydantic %s — imported", pydantic.__version__)

        from pydantic import BaseModel  # noqa: PLC0415

        class DataPipeline(BaseModel):
            name: str
            version: str
            rows_processed: int
            success: bool = True

        pipeline = DataPipeline(
            name="etl_daily",
            version="1.0.0",
            rows_processed=1_500_000,
        )
        dumped = pipeline.model_dump()
        assert dumped["rows_processed"] == 1_500_000
        log.debug("pydantic model_dump: %s", dumped)
        log.info("[PASS] pydantic — BaseModel definition + model_dump() OK")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] pydantic — %s", exc)
        return False


def test_matplotlib() -> bool:
    """Import matplotlib, generate a figure using the Agg (non-GUI) backend."""
    try:
        import matplotlib  # noqa: PLC0415

        matplotlib.use("Agg")  # Non-interactive backend — safe in headless envs
        import matplotlib.pyplot as plt  # noqa: PLC0415

        log.info(
            "[PASS] matplotlib %s — imported (Agg backend)", matplotlib.__version__
        )

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([1, 2, 3, 4], [10, 24, 18, 35], marker="o", label="Series A")
        ax.set_title("Smoke Test")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()

        import io  # noqa: PLC0415

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        size_kb = buf.tell() / 1024
        plt.close(fig)

        log.debug("matplotlib figure size: %.1f KB", size_kb)
        log.info("[PASS] matplotlib — Figure + savefig OK (%.1f KB)", size_kb)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] matplotlib — %s", exc)
        return False


def test_plotly() -> bool:
    """Import plotly and validate go.Figure JSON serialization."""
    try:
        import plotly  # noqa: PLC0415
        import plotly.graph_objects as go  # noqa: PLC0415

        log.info("[PASS] plotly %s — imported", plotly.__version__)

        fig = go.Figure(
            data=[go.Bar(x=["Q1", "Q2", "Q3", "Q4"], y=[120, 180, 95, 210])],
            layout=go.Layout(title="Quarterly Revenue Smoke Test"),
        )
        json_str = fig.to_json()
        assert "Q1" in json_str, "Serialized JSON missing expected data"
        log.debug("plotly JSON length: %d chars", len(json_str))
        log.info("[PASS] plotly — go.Figure + to_json() OK")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] plotly — %s", exc)
        return False


def test_tqdm() -> bool:
    """Import tqdm and run a progress bar over a small iterable."""
    try:
        import tqdm  # noqa: PLC0415

        log.info("[PASS] tqdm %s — imported", tqdm.__version__)

        import io as _io  # noqa: PLC0415

        devnull = _io.StringIO()  # Suppress bar output from polluting log

        start = time.perf_counter()
        total = 0
        for i in tqdm.tqdm(range(500), file=devnull, desc="smoke"):
            total += i
        elapsed = time.perf_counter() - start

        assert total == sum(range(500))
        log.info("[PASS] tqdm — progress bar iteration OK (%.3f s)", elapsed)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("[FAIL] tqdm — %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def main() -> int:
    log.info("=" * 70)
    log.info("Phase 2 — Data Engineering Lite Stack Validation")
    log.info("Author  : Dr. Ceasar Jackson Jr.")
    log.info("Python  : %s", sys.version.split()[0])
    log.info("=" * 70)

    checks = [
        ("numpy", test_numpy),
        ("pandas", test_pandas),
        ("polars", test_polars),
        ("duckdb", test_duckdb),
        ("sqlalchemy", test_sqlalchemy),
        ("pydantic", test_pydantic),
        ("matplotlib", test_matplotlib),
        ("plotly", test_plotly),
        ("tqdm", test_tqdm),
    ]

    results: dict[str, bool] = {}
    for name, fn in checks:
        log.info("-" * 50)
        log.info("Testing: %s", name)
        results[name] = fn()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    log.info("=" * 70)
    log.info("Phase 2 Summary")
    log.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for pkg, result in results.items():
        status = "PASS" if result else "FAIL"
        if result:
            log.info("  [%s] %s", status, pkg)
        else:
            log.error("  [%s] %s", status, pkg)

    log.info("-" * 70)
    if failed == 0:
        log.info("All %d packages validated.  Stack is operational.", passed)
        return 0
    else:
        log.error(
            "%d of %d packages FAILED.  Review errors above.",
            failed,
            len(results),
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
