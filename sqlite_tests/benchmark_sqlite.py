import sqlite3
import time

conn = sqlite3.connect(":memory:")
cur = conn.cursor()

start = time.time()

cur.execute("""
CREATE TABLE numbers(
    id INTEGER,
    value REAL
)
""")

rows = [(i, i * 0.5) for i in range(100000)]

cur.executemany(
    "INSERT INTO numbers VALUES (?,?)",
    rows
)

conn.commit()

result = cur.execute("""
SELECT
    AVG(value),
    MIN(value),
    MAX(value)
FROM numbers
""").fetchone()

elapsed = time.time() - start

print("BENCHMARK TEST")
print(result)
print("Elapsed:", round(elapsed, 3), "seconds")

conn.close()
