import sqlite3
from pathlib import Path

db_file = "sqlite_tests/employees.db"

# Ensure a clean database for every test run
if Path(db_file).exists():
    Path(db_file).unlink()

conn = sqlite3.connect(db_file)
cur = conn.cursor()

cur.execute("""
CREATE TABLE employees(
    id INTEGER,
    name TEXT
)
""")

cur.execute("INSERT INTO employees VALUES (?,?)", (1, "Alice"))

conn.commit()

count = cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0]

print("FILE DB TEST")
print("Rows:", count)

conn.close()

print("Database exists:", Path(db_file).exists())
