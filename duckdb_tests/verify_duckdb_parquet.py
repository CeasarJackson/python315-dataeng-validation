import duckdb

con = duckdb.connect()

result = con.execute("""
SELECT *
FROM read_parquet('employees.parquet')
""").fetchdf()

print(result)

con.close()
