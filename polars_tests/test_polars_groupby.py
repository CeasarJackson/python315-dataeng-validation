"""test_polars_groupby.py — Polars groupby and aggregation under Python 3.15."""

import polars as pl


def test_polars_group_by_sum():
    """Polars groups by a column and sums another."""
    df = pl.DataFrame(
        {
            "dept": ["IT", "IT", "HR", "HR"],
            "salary": [100, 120, 75, 80],
        }
    )
    result = df.group_by("dept").agg(pl.col("salary").sum()).sort("dept")
    assert len(result) == 2
    it_row = result.filter(pl.col("dept") == "IT")
    assert it_row["salary"][0] == 220


def test_polars_group_by_count():
    """Polars counts rows per group."""
    df = pl.DataFrame({"category": ["A", "A", "B", "B", "B"]})
    result = df.group_by("category").agg(pl.len().alias("n")).sort("category")
    assert result.filter(pl.col("category") == "A")["n"][0] == 2
    assert result.filter(pl.col("category") == "B")["n"][0] == 3


def test_polars_group_by_multiple_aggs():
    """Polars computes multiple aggregations in one group_by."""
    df = pl.DataFrame(
        {
            "g": ["x", "x", "y"],
            "v": [1.0, 3.0, 2.0],
        }
    )
    result = df.group_by("g").agg(
        [
            pl.col("v").mean().alias("mean_v"),
            pl.col("v").max().alias("max_v"),
        ]
    )
    x = result.filter(pl.col("g") == "x")
    assert x["mean_v"][0] == 2.0
    assert x["max_v"][0] == 3.0
