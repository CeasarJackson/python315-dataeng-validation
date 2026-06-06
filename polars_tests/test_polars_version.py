"""test_polars_version.py — Polars version and import validation."""

import polars as pl


def test_polars_version():
    """Polars exposes a version string."""
    assert pl.__version__
    parts = pl.__version__.split(".")
    assert len(parts) >= 2


def test_polars_dataframe_creation():
    """Polars creates a DataFrame from a dict."""
    df = pl.DataFrame({"id": [1, 2, 3]})
    assert len(df) == 3
    assert df.columns == ["id"]
