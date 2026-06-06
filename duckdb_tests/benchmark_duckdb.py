import duckdb
import time

con = duckdb.connect(":memory:")

start = time.time()

con.execute("""
CREATE TABLE numbers AS
SELECT
    range AS id,
    random() * 1000 AS value
FROM range(1000000)
""")

result = con.execute("""
SELECT
    AVG(value),
    MIN(value),
    MAX(value)
FROM numbers
""").fetchone()

elapsed = time.time() - start

print("Result:", result)
print("Elapsed:", round(elapsed, 3), "seconds")
