"""test_duckdb_native_parquet.py — DuckDB native Parquet I/O under Python 3.15."""
import duckdb
import tempfile
import pathlib


def test_duckdb_parquet_write_and_read(tmp_path):
    """DuckDB writes and reads Parquet files without pyarrow."""
    parquet_file = str(tmp_path / "employees.parquet")
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE employees AS SELECT * FROM (VALUES
            (1,'Alice',100000),(2,'Bob',125000),(3,'Charlie',95000)
        ) t(id,name,salary)
    """)
    con.execute(f"COPY employees TO '{parquet_file}' (FORMAT PARQUET)")
    assert pathlib.Path(parquet_file).exists()
    assert pathlib.Path(parquet_file).stat().st_size > 0
    result = con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquet_file}')").fetchone()
    assert result[0] == 3
    con.close()


def test_duckdb_parquet_schema(tmp_path):
    """DuckDB preserves schema through Parquet round-trip."""
    parquet_file = str(tmp_path / "schema_test.parquet")
    con = duckdb.connect()
    con.execute("CREATE TABLE t AS SELECT 42 AS n, 'hello' AS s, 3.14 AS f")
    con.execute(f"COPY t TO '{parquet_file}' (FORMAT PARQUET)")
    row = con.execute(f"SELECT * FROM read_parquet('{parquet_file}')").fetchone()
    assert row[0] == 42
    assert row[1] == "hello"
    assert abs(float(row[2]) - 3.14) < 0.001
    con.close()
