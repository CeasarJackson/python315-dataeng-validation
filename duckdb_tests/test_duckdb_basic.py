import duckdb

con = duckdb.connect(":memory:")

con.execute("""
CREATE TABLE employees(
    id INTEGER,
    name VARCHAR,
    salary DOUBLE
)
""")

con.execute("""
INSERT INTO employees VALUES
(1,'Alice',100000),
(2,'Bob',125000),
(3,'Charlie',95000)
""")

result = con.execute("""
SELECT *
FROM employees
ORDER BY salary DESC
""").fetchall()

print(result)

con.close()
