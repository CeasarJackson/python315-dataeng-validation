import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()

cur.execute("""
CREATE TABLE salaries(
    department TEXT,
    salary REAL
)
""")

cur.executemany(
    "INSERT INTO salaries VALUES (?,?)",
    [
        ("IT",100000),
        ("IT",120000),
        ("HR",75000),
        ("HR",80000),
        ("Finance",90000),
    ]
)

rows = cur.execute("""
SELECT
    department,
    ROUND(AVG(salary),2) AS avg_salary
FROM salaries
GROUP BY department
ORDER BY avg_salary DESC
""").fetchall()

print("AGGREGATION TEST")
for row in rows:
    print(row)

conn.close()
