import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()

cur.execute("""
CREATE TABLE employees(
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary REAL
)
""")

cur.executemany(
    "INSERT INTO employees VALUES (?,?,?)",
    [
        (1, "Alice", 100000),
        (2, "Bob", 125000),
        (3, "Charlie", 95000),
    ]
)

conn.commit()

rows = cur.execute("""
SELECT *
FROM employees
ORDER BY salary DESC
""").fetchall()

print("CRUD TEST")
for row in rows:
    print(row)

conn.close()
