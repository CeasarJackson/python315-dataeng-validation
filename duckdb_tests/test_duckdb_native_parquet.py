import duckdb

con = duckdb.connect()

con.execute("""
CREATE TABLE employees AS
SELECT *
FROM (
VALUES
(1,'Alice',100000),
(2,'Bob',125000),
(3,'Charlie',95000)
) t(id,name,salary)
""")

con.execute("""
COPY employees
TO 'employees.parquet'
(FORMAT PARQUET)
""")

print("Parquet file written successfully.")

con.close()
