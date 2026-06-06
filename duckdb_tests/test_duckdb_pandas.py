"""test_duckdb_pandas.py — DuckDB + Pandas integration under Python 3.15."""
import duckdb
import pandas as pd


def test_duckdb_query_pandas_dataframe():
    """DuckDB queries a Pandas DataFrame directly via SQL."""
    df = pd.DataFrame({
        "department": ["IT", "IT", "HR", "HR", "Finance"],
        "salary": [100000, 120000, 75000, 80000, 90000],
    })
    result = duckdb.sql("""
        SELECT department, AVG(salary) AS avg_salary
        FROM df
        GROUP BY department
        ORDER BY avg_salary DESC
    """).df()
    assert len(result) == 3
    assert result.iloc[0]["department"] == "IT"
    assert result.iloc[0]["avg_salary"] == 110000.0


def test_duckdb_pandas_roundtrip():
    """DuckDB converts query results back to a Pandas DataFrame."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    result = duckdb.sql("SELECT x, y, x + y AS z FROM df").df()
    assert list(result.columns) == ["x", "y", "z"]
    assert list(result["z"]) == [5, 7, 9]
